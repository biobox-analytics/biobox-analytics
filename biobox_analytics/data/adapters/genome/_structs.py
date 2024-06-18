from __future__ import annotations 
from datetime import (
    datetime,
    date
)
from decimal import Decimal 
from enum import Enum 
import re
import sys
from pydantic.version import VERSION  as PYDANTIC_VERSION 
from typing import (
    Any,
    List,
    Literal,
    Dict,
    Optional,
    Union,
    Generic,
    Iterable,
    TypeVar,
    get_args
)
if sys.version_info.minor > 8:
    from typing import Annotated 
else:
    from typing_extensions import Annotated 

if int(PYDANTIC_VERSION[0])>=2:
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

from pydantic import GetCoreSchemaHandler 
from pydantic_core import (
    CoreSchema,
    core_schema
)
metamodel_version = "None"
version = "None"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )
    pass


_T = TypeVar("_T")

_RecursiveListType = Iterable[Union[_T, Iterable["_RecursiveListType"]]]

class AnyShapeArrayType(Generic[_T]):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        # double-nested parameterized types here
        # source_type: List[Union[T,List[...]]]
        item_type = Any if get_args(get_args(source_type)[0])[0] is _T else get_args(get_args(source_type)[0])[0]

        item_schema = handler.generate_schema(item_type)
        if item_schema.get("type", "any") != "any":
            item_schema["strict"] = True

        if item_type is Any:
            # Before python 3.11, `Any` type was a special object without a __name__
            item_name = "Any"
        else:
            item_name = item_type.__name__

        array_ref = f"any-shape-array-{item_name}"

        schema = core_schema.definitions_schema(
            core_schema.list_schema(core_schema.definition_reference_schema(array_ref)),
            [
                core_schema.union_schema(
                    [
                        core_schema.list_schema(core_schema.definition_reference_schema(array_ref)),
                        item_schema,
                    ],
                    ref=array_ref,
                )
            ],
        )

        return schema


AnyShapeArray = Annotated[_RecursiveListType, AnyShapeArrayType]

class Object(ConfiguredBaseModel):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class Node(ConfiguredBaseModel):
    id: str = Field(...)
    labels: Optional[AnyShapeArray[str]] = Field(None)


class Edge(ConfiguredBaseModel):
    from_: Object = Field(...)
    to: Object = Field(...)
    label: str = Field(...)


class Sample(Object):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class Donor(Object):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class Experiment(Object):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class EpigeneticExperiment(Experiment):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class Genome(Object):
    assembly: Optional[str] = Field(None)
    taxon: int = Field(...)
    species: str = Field(..., description="""Is the full species name is lower case (e.g. homo sapiens)""")
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class GenomicInterval(Object):
    chr: Optional[str] = Field(None, description="""Name of the chromosome (or contig, scaffold, etc.)""")
    start: Optional[int] = Field(None, description="""The starting position of the feature in the chromosome or scaffold. The first base in a chromosome is numbered 1""")
    end: Optional[int] = Field(None, description="""The ending position of the feature in the chromosome or scaffold. The chromEnd base is not included in the display of the feature. For example, the first 100 bases of a chromosome are defined as chromStart=1, chromEnd=100,  and span the bases numbered 1-100.""")
    taxon: int = Field(...)
    species: str = Field(..., description="""Is the full species name is lower case (e.g. homo sapiens)""")
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class Gene(Object):
    """
    A region (or regions) that includes all of the sequence elements necessary to encode a functional transcript.  A gene may include regulatory regions, transcribed regions and/or other functional sequence regions.
    """
    chr: Optional[str] = Field(None, description="""Name of the chromosome (or contig, scaffold, etc.)""")
    start: Optional[int] = Field(None, description="""The starting position of the feature in the chromosome or scaffold. The first base in a chromosome is numbered 1""")
    end: Optional[int] = Field(None, description="""The ending position of the feature in the chromosome or scaffold. The chromEnd base is not included in the display of the feature. For example, the first 100 bases of a chromosome are defined as chromStart=1, chromEnd=100,  and span the bases numbered 1-100.""")
    assembly: Optional[str] = Field(None)
    taxon: int = Field(...)
    strand: Optional[str] = Field(None, description="""+/- to denote strand or orientation (whenever applicable). Use \".\" if no orientation is assigned.""")
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class Transcript(Object):
    chr: Optional[str] = Field(None, description="""Name of the chromosome (or contig, scaffold, etc.)""")
    start: Optional[int] = Field(None, description="""The starting position of the feature in the chromosome or scaffold. The first base in a chromosome is numbered 1""")
    end: Optional[int] = Field(None, description="""The ending position of the feature in the chromosome or scaffold. The chromEnd base is not included in the display of the feature. For example, the first 100 bases of a chromosome are defined as chromStart=1, chromEnd=100,  and span the bases numbered 1-100.""")
    assembly: Optional[str] = Field(None)
    taxon: int = Field(...)
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class Protein(Object):
    assembly: Optional[str] = Field(None)
    taxon: int = Field(...)
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class GenomeContainsInterval(Edge):
    from_: Genome = Field(...)
    to: GenomicInterval = Field(...)
    label: str = Field(...)


class HasTranslation(Edge):
    from_: Transcript = Field(...)
    to: Protein = Field(...)
    label: str = Field(...)


class TranscribedTo(Edge):
    from_: Gene = Field(...)
    to: Transcript = Field(...)
    label: str = Field(...)


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
Object.model_rebuild()
Node.model_rebuild()
Edge.model_rebuild()
Sample.model_rebuild()
Donor.model_rebuild()
Experiment.model_rebuild()
EpigeneticExperiment.model_rebuild()
Genome.model_rebuild()
GenomicInterval.model_rebuild()
Gene.model_rebuild()
Transcript.model_rebuild()
Protein.model_rebuild()
GenomeContainsInterval.model_rebuild()
HasTranslation.model_rebuild()
TranscribedTo.model_rebuild()

