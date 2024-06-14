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


class ModificationTypes(str, Enum):
    PTM = "PTM"


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


class CellType(Object):
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


class ChipSeq(EpigeneticExperiment):
    """
    A method to determine the genomic regions that proteins bind to.
    """
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class NarrowPeak(Object):
    """
    Peaks of signal enrichment based on pooled, normalized (interpreted) data. It is a BED6+4 format.
    """
    chr: Optional[str] = Field(None, description="""Name of the chromosome (or contig, scaffold, etc.)""")
    start: Optional[int] = Field(None, description="""The starting position of the feature in the chromosome or scaffold. The first base in a chromosome is numbered 1""")
    end: Optional[int] = Field(None, description="""The ending position of the feature in the chromosome or scaffold. The chromEnd base is not included in the display of the feature. For example, the first 100 bases of a chromosome are defined as chromStart=1, chromEnd=100,  and span the bases numbered 1-100.""")
    strand: Optional[str] = Field(None, description="""+/- to denote strand or orientation (whenever applicable). Use \".\" if no orientation is assigned.""")
    score: Optional[int] = Field(None, description="""Indicates how dark the peak will be displayed in the browser (0-1000).  If all scores were \"'0\"' when the data were submitted to the DCC,  the DCC assigned scores 1-1000 based on signal value.  Ideally the average signalValue per base spread is between 100-1000.""")
    signalValue: Optional[float] = Field(None, description="""Measurement of overall (usually, average) enrichment for the region.""")
    pValue: Optional[float] = Field(None, description="""Measurement of statistical significance (-log10). Use -1 if no pValue is assigned.""")
    qValue: Optional[float] = Field(None, description="""Measurement of statistical significance using false discovery rate (-log10). Use -1 if no qValue is assigned.""")
    peak: Optional[int] = Field(None, description="""Point-source called for this peak; 0-based offset from_ chromStart. Use -1 if no point-source called.""")
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class AssayTargetOn(Edge):
    """
    Describes the target for the immuno-precipitation and/or pull down assay.
    """
    modification_type: Optional[ModificationTypes] = Field(None)
    modification: Optional[str] = Field(None)
    position: Optional[int] = Field(None)
    residue: Optional[str] = Field(None)
    from_: ChipSeq = Field(...)
    to: Protein = Field(...)
    label: str = Field(...)


class HasExperiment(Edge):
    from_: Sample = Field(...)
    to: Experiment = Field(...)
    label: str = Field(...)


class HasPeak(Edge):
    from_: CellBarcode = Field(...)
    to: NarrowPeak = Field(...)
    label: str = Field(...)


class PeakStartOn(Edge):
    """
    maps the starting position of the peak coverage interval
    """
    from_: ChipSeq = Field(...)
    to: GenomicInterval = Field(...)
    label: str = Field(...)


class PeakEndOn(Edge):
    """
    maps the end position of the peak coverage interval
    """
    from_: ChipSeq = Field(...)
    to: GenomicInterval = Field(...)
    label: str = Field(...)


class CellBarcode(Object):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class SingleCellExperiment(Experiment):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class SingleCellRNAseqExperiment(SingleCellExperiment):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class SingleNucleiRNAseqExperiment(SingleCellRNAseqExperiment):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class SingleCellATACseqExperiment(SingleCellExperiment):
    uuid: Optional[str] = Field(None)
    displayName: str = Field(...)
    description: Optional[str] = Field(None)
    dateCreated: Optional[datetime ] = Field(None)
    dateUpdated: Optional[datetime ] = Field(None)


class ContainsCell(Edge):
    from_: SingleCellExperiment = Field(...)
    to: CellBarcode = Field(...)
    label: str = Field(...)


class Expresses(Edge):
    from_: CellBarcode = Field(...)
    to: Gene = Field(...)
    label: str = Field(...)


class HasCellType(Edge):
    from_: CellBarcode = Field(...)
    to: CellType = Field(...)
    label: str = Field(...)


class HasGenePeak(Edge):
    from_: CellBarcode = Field(...)
    to: Gene = Field(...)
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
CellType.model_rebuild()
Genome.model_rebuild()
GenomicInterval.model_rebuild()
Gene.model_rebuild()
Transcript.model_rebuild()
Protein.model_rebuild()
GenomeContainsInterval.model_rebuild()
HasTranslation.model_rebuild()
TranscribedTo.model_rebuild()
ChipSeq.model_rebuild()
NarrowPeak.model_rebuild()
AssayTargetOn.model_rebuild()
HasExperiment.model_rebuild()
HasPeak.model_rebuild()
PeakStartOn.model_rebuild()
PeakEndOn.model_rebuild()
CellBarcode.model_rebuild()
SingleCellExperiment.model_rebuild()
SingleCellRNAseqExperiment.model_rebuild()
SingleNucleiRNAseqExperiment.model_rebuild()
SingleCellATACseqExperiment.model_rebuild()
ContainsCell.model_rebuild()
Expresses.model_rebuild()
HasCellType.model_rebuild()
HasGenePeak.model_rebuild()

