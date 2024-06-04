from __future__ import annotations
from datetime import (
    datetime,
    date
)
from decimal import Decimal
from enum import Enum
import re
import sys
from pydantic.version import VERSION as PYDANTIC_VERSION

if int(PYDANTIC_VERSION[0]) >= 2:
    from pydantic import (
        BaseModel,
        ConfigDict,
        Field,
        field_validator
    )
else:
    from pydantic import (
        BaseModel,
        Field,
        validator
    )

from typing import (
    Any,
    List,
    Literal,
    Dict,
    Optional,
    Union,
    Generic,
    TypeVar,
    _GenericAlias
)

metamodel_version = "None"
version = "None"


class WeakRefShimBaseModel(BaseModel):
    __slots__ = '__weakref__'


class ConfiguredBaseModel(WeakRefShimBaseModel,
                          validate_assignment=True,
                          validate_all=True,
                          underscore_attrs_are_private=True,
                          extra="forbid",
                          arbitrary_types_allowed=True,
                          use_enum_values=True):
    pass


_T = TypeVar("_T")


class AnyShapeArray(Generic[_T]):
    type_: Type[Any] = Any

    def __class_getitem__(cls, item):
        alias = type(f"AnyShape_{str(item.__name__)}", (AnyShapeArray,), {"type_": item})
        alias.type_ = item
        return alias

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        try:
            item_type = field_schema["allOf"][0]["type"]
            type_schema = {"type": item_type}
            del field_schema["allOf"]
        except KeyError as e:
            if "allOf" in str(e):
                item_type = "Any"
                type_schema = {}
            else:
                raise e

        array_id = f"#any-shape-array-{item_type}"
        field_schema["anyOf"] = [
            type_schema,
            {"type": "array", "items": {"$ref": array_id}},
        ]
        field_schema["$id"] = array_id

    @classmethod
    def validate(cls, v: Union[List[_T], list]):
        if str(type(v)) == "<class 'numpy.ndarray'>":
            v = v.tolist()

        if not isinstance(v, list):
            raise TypeError(f"Must be a list of lists! got {v}")

        def _validate(_v: Union[List[_T], list]):
            for item in _v:
                if isinstance(item, list):
                    _validate(item)
                else:
                    try:
                        anytype = cls.type_.__name__ in ("AnyType", "Any")
                    except AttributeError:
                        # in python 3.8 and 3.9, `typing.Any` has no __name__
                        anytype = str(cls.type_).split(".")[-1] in ("AnyType", "Any")

                    if not anytype and not isinstance(item, cls.type_):
                        raise TypeError(
                            (
                                f"List items must be list of lists, or the type used in "
                                f"the subscript ({cls.type_}. Got item {item} and outer value {v}"
                            )
                        )
            return _v

        return _validate(v)


class Object(ConfiguredBaseModel):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


class Node(ConfiguredBaseModel):
    _id: str = Field(...)
    labels: Optional[AnyShapeArray[str]] = Field(None)


class Edge(ConfiguredBaseModel):
    _from: Object = Field(...)
    to: Object = Field(...)
    label: str = Field(...)


class Genome(Object):
    assembly: Optional[str] = Field(None)
    taxon: int = Field(...)
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


class GenomicInterval(Object):
    chr: Optional[str] = Field(None, description="""Name of the chromosome (or contig, scaffold, etc.)""")
    start: Optional[int] = Field(None,
                                 description="""The starting position of the feature in the chromosome or scaffold. The first base in a chromosome is numbered 1""")
    end: Optional[int] = Field(None,
                               description="""The ending position of the feature in the chromosome or scaffold. The chromEnd base is not included in the display of the feature. For example, the first 100 bases of a chromosome are defined as chromStart=1, chromEnd=100,  and span the bases numbered 1-100.""")
    taxon: int = Field(...)
    species: str = Field(..., description="""Is the full species name is lower case (e.g. homo sapiens)""")
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


class Gene(Object):
    """
    A region (or regions) that includes all of the sequence elements necessary to encode a functional transcript.  A gene may include regulatory regions, transcribed regions and/or other functional sequence regions.
    """
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


class Transcript(Object):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


class Protein(Object):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


class HasTranslation(Edge):
    _from: Transcript = Field(...)
    to: Protein = Field(...)
    label: str = Field(...)


class CellularComponent(Object):
    """
    A location relative to cellular compartments and structures occupied by a macromolecular machine. There are three types of cellular components described in the gene ontology: (1) the cellular anatomical entity where a gene product carries out a molecular function (e.g. plasma membrane cytoskeleton) or membrane-enclosed  compartments (e.g. mitochondrion); (2) virion components where viral proteins act and (3) the stable macromolecular complexes of which gene product are parts (e.g. the clathrin complex)
    """
    database_cross_reference: Optional[AnyShapeArray[str]] = Field(None)
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


class BiologicalProcess(Object):
    """
    A biological process is the execution of a genetically-encoded biological module or program.  It consists of all the steps required to achieve the specific biological objective of the module.  A biological process is accomplished by a particular set of molecular functions carried out by specific  gene products (or macromolecular complexes) often in a highly regulated manner and in a  particular temporal sequence.
    """
    database_cross_reference: Optional[AnyShapeArray[str]] = Field(None)
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


class MolecularFunction(Object):
    """
    A molecular process that can be carried out by the action of a single macromolecular machine  usually via direct physical interactions with other molecular entities. Function in this sense  denotes an action or activity that a gene product (or a complex) performs
    """
    database_cross_reference: Optional[AnyShapeArray[str]] = Field(None)
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


class Enables(Edge):
    _from: Gene = Field(...)
    to: MolecularFunction = Field(...)
    label: str = Field(...)


class LocatedIn(Edge):
    _from: Gene = Field(...)
    to: CellularComponent = Field(...)
    label: str = Field(...)


class InvolvedIn(Edge):
    _from: Gene = Field(...)
    to: BiologicalProcess = Field(...)
    label: str = Field(...)


class PartOf(Edge):
    _from: Gene = Field(...)
    to: CellularComponent = Field(...)
    label: str = Field(...)


class NotEnables(Edge):
    _from: Gene = Field(...)
    to: MolecularFunction = Field(...)
    label: str = Field(...)


class NotInvolvedIn(Edge):
    _from: Gene = Field(...)
    to: BiologicalProcess = Field(...)
    label: str = Field(...)


class IsActiveIn(Edge):
    _from: Gene = Field(...)
    to: CellularComponent = Field(...)
    label: str = Field(...)


class NotColocalizesWith(Edge):
    _from: Gene = Field(...)
    to: CellularComponent = Field(...)
    label: str = Field(...)


class ColocalizesWith(Edge):
    _from: Gene = Field(...)
    to: CellularComponent = Field(...)
    label: str = Field(...)


class ActsUpstreamOfOrWithin(Edge):
    _from: Gene = Field(...)
    to: BiologicalProcess = Field(...)
    label: str = Field(...)


class ContributesTo(Edge):
    _from: Gene = Field(...)
    to: MolecularFunction = Field(...)
    label: str = Field(...)


class NotLocatedIn(Edge):
    _from: Gene = Field(...)
    to: CellularComponent = Field(...)
    label: str = Field(...)


class NotPartOf(Edge):
    _from: Gene = Field(...)
    to: CellularComponent = Field(...)
    label: str = Field(...)


class ActsUpstreamOfPositiveEffect(Edge):
    _from: Gene = Field(...)
    to: BiologicalProcess = Field(...)
    label: str = Field(...)


class NotActsUpstreamOfOrWithin(Edge):
    _from: Gene = Field(...)
    to: BiologicalProcess = Field(...)
    label: str = Field(...)


class ActsUpstreamOf(Edge):
    _from: Gene = Field(...)
    to: BiologicalProcess = Field(...)
    label: str = Field(...)


class ActsUpstreamOfNegativeEffect(Edge):
    _from: Gene = Field(...)
    to: BiologicalProcess = Field(...)
    label: str = Field(...)


class ActsUpstreamOfOrWithinPositiveEffect(Edge):
    _from: Gene = Field(...)
    to: BiologicalProcess = Field(...)
    label: str = Field(...)


class ActsUpstreamOfOrWithinNegativeEffect(Edge):
    _from: Gene = Field(...)
    to: BiologicalProcess = Field(...)
    label: str = Field(...)


class NotContributesTo(Edge):
    _from: Gene = Field(...)
    to: MolecularFunction = Field(...)
    label: str = Field(...)


class NotActsUpstreamOfOrWithinNegativeEffect(Edge):
    _from: Gene = Field(...)
    to: BiologicalProcess = Field(...)
    label: str = Field(...)


class NotIsActiveIn(Edge):
    _from: Gene = Field(...)
    to: CellularComponent = Field(...)
    label: str = Field(...)


# Update forward refs
# see https://pydantic-docs.helpmanual.io/usage/postponed_annotations/
Object.update_forward_refs()
Node.update_forward_refs()
Edge.update_forward_refs()
Genome.update_forward_refs()
GenomicInterval.update_forward_refs()
Gene.update_forward_refs()
Transcript.update_forward_refs()
Protein.update_forward_refs()
HasTranslation.update_forward_refs()
CellularComponent.update_forward_refs()
BiologicalProcess.update_forward_refs()
MolecularFunction.update_forward_refs()
Enables.update_forward_refs()
LocatedIn.update_forward_refs()
InvolvedIn.update_forward_refs()
PartOf.update_forward_refs()
NotEnables.update_forward_refs()
NotInvolvedIn.update_forward_refs()
IsActiveIn.update_forward_refs()
NotColocalizesWith.update_forward_refs()
ColocalizesWith.update_forward_refs()
ActsUpstreamOfOrWithin.update_forward_refs()
ContributesTo.update_forward_refs()
NotLocatedIn.update_forward_refs()
NotPartOf.update_forward_refs()
ActsUpstreamOfPositiveEffect.update_forward_refs()
NotActsUpstreamOfOrWithin.update_forward_refs()
ActsUpstreamOf.update_forward_refs()
ActsUpstreamOfNegativeEffect.update_forward_refs()
ActsUpstreamOfOrWithinPositiveEffect.update_forward_refs()
ActsUpstreamOfOrWithinNegativeEffect.update_forward_refs()
NotContributesTo.update_forward_refs()
NotActsUpstreamOfOrWithinNegativeEffect.update_forward_refs()
NotIsActiveIn.update_forward_refs()
