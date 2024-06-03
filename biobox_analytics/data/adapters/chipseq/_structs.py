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


class ModificationTypes(str, Enum):
    PTM = "PTM"


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


class Sample(Object):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


class Donor(Object):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


class Experiment(Object):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


class EpigeneticExperiment(Experiment):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


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
                                 description="""The starting position of the feature in the chromosome or scaffold. The first base in a chromosome is numbered 0""")
    end: Optional[int] = Field(None,
                               description="""The ending position of the feature in the chromosome or scaffold. The chromEnd base is not included in the display of the feature. For example, the first 100 bases of a chromosome are defined as chromStart=0, chromEnd=100,  and span the bases numbered 0-99.""")
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


class ChipSeq(EpigeneticExperiment):
    """
    A method to determine the genomic regions that proteins bind to.
    """
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


class ModifiedProtein(Protein):
    """
    A protein that has a post-translational modification.
    """
    modification_type: Optional[ModificationTypes] = Field(None)
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime] = Field(None)
    dateUpdated: Optional[datetime] = Field(None)


class NarrowPeakOn(Edge):
    """
    Peaks of signal enrichment based on pooled, normalized (interpreted) data. It is a BED6+4 format.
    """
    chr: Optional[str] = Field(None, description="""Name of the chromosome (or contig, scaffold, etc.)""")
    start: Optional[int] = Field(None,
                                 description="""The starting position of the feature in the chromosome or scaffold. The first base in a chromosome is numbered 0""")
    end: Optional[int] = Field(None,
                               description="""The ending position of the feature in the chromosome or scaffold. The chromEnd base is not included in the display of the feature. For example, the first 100 bases of a chromosome are defined as chromStart=0, chromEnd=100,  and span the bases numbered 0-99.""")
    strand: Optional[str] = Field(None,
                                  description="""+/- to denote strand or orientation (whenever applicable). Use \".\" if no orientation is assigned.""")
    score: Optional[int] = Field(None,
                                 description="""Indicates how dark the peak will be displayed in the browser (0-1000).  If all scores were \"'0\"' when the data were submitted to the DCC,  the DCC assigned scores 1-1000 based on signal value.  Ideally the average signalValue per base spread is between 100-1000.""")
    signalValue: Optional[float] = Field(None,
                                         description="""Measurement of overall (usually, average) enrichment for the region.""")
    pValue: Optional[float] = Field(None,
                                    description="""Measurement of statistical significance (-log10). Use -1 if no pValue is assigned.""")
    qValue: Optional[float] = Field(None,
                                    description="""Measurement of statistical significance using false discovery rate (-log10). Use -1 if no qValue is assigned.""")
    peak: Optional[int] = Field(None,
                                description="""Point-source called for this peak; 0-based offset _from chromStart. Use -1 if no point-source called.""")
    _from: EpigeneticExperiment = Field(...)
    to: GenomicInterval = Field(...)
    label: str = Field(...)


class IsAModifiedFormOf(Edge):
    """
    A gene has a translation to a protein.
    """
    _from: ModifiedProtein = Field(...)
    to: Protein = Field(...)
    label: str = Field(...)


class AssayTargetOn(Edge):
    """
    Describes the target for the immuno-precipitation and/or pull down assay.
    """
    _from: ChipSeq = Field(...)
    to: Protein = Field(...)
    label: str = Field(...)


# Update forward refs
# see https://pydantic-docs.helpmanual.io/usage/postponed_annotations/
Object.update_forward_refs()
Node.update_forward_refs()
Edge.update_forward_refs()
Sample.update_forward_refs()
Donor.update_forward_refs()
Experiment.update_forward_refs()
EpigeneticExperiment.update_forward_refs()
Genome.update_forward_refs()
GenomicInterval.update_forward_refs()
Gene.update_forward_refs()
Transcript.update_forward_refs()
Protein.update_forward_refs()
HasTranslation.update_forward_refs()
ChipSeq.update_forward_refs()
ModifiedProtein.update_forward_refs()
NarrowPeakOn.update_forward_refs()
IsAModifiedFormOf.update_forward_refs()
AssayTargetOn.update_forward_refs()
