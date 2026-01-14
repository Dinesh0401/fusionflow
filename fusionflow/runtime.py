"""Runtime registry for FusionFlow temporal specifications"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .ast_nodes import (
    DatasetDeclaration,
    DatasetReference,
    PipelineDefinition,
    ModelDefinition,
    ExperimentDefinition,
    MergeStatement,
)


@dataclass
class TimelineSpec:
    name: str
    description: Optional[str] = None
    parent: Optional[str] = None
    experiments: Dict[str, ExperimentDefinition] = field(default_factory=dict)


class Runtime:
    def __init__(self):
        self.datasets: Dict[Tuple[str, str], DatasetDeclaration] = {}
        self.pipelines: Dict[str, PipelineDefinition] = {}
        self.models: Dict[str, ModelDefinition] = {}
        self.timelines: Dict[str, TimelineSpec] = {
            'main': TimelineSpec(name='main', description='Primary timeline', parent=None)
        }
        self.experiments_index: Dict[Tuple[str, str], ExperimentDefinition] = {}
        self.merges: List[MergeStatement] = []
        self.current_timeline = 'main'

    @staticmethod
    def _dataset_key(name: str, version: str) -> Tuple[str, str]:
        return (name, version)

    def register_dataset(self, declaration: DatasetDeclaration):
        key = self._dataset_key(declaration.name, declaration.version)
        if key in self.datasets:
            raise ValueError(f"Dataset '{declaration.name}' version '{declaration.version}' already declared")
        self.datasets[key] = declaration

    def get_dataset(self, reference: DatasetReference) -> Optional[DatasetDeclaration]:
        return self.datasets.get(self._dataset_key(reference.name, reference.version))

    def register_pipeline(self, definition: PipelineDefinition):
        if definition.name in self.pipelines:
            raise ValueError(f"Pipeline '{definition.name}' already declared")
        if not self.get_dataset(definition.source):
            raise ValueError(
                f"Pipeline '{definition.name}' references unknown dataset '{definition.source.name}' version '{definition.source.version}'"
            )
        self.pipelines[definition.name] = definition

    def register_model(self, definition: ModelDefinition):
        if definition.name in self.models:
            raise ValueError(f"Model '{definition.name}' already declared")
        self.models[definition.name] = definition

    def ensure_pipeline(self, name: str):
        if name not in self.pipelines:
            raise ValueError(f"Pipeline '{name}' is not defined")

    def ensure_model(self, name: str):
        if name not in self.models:
            raise ValueError(f"Model '{name}' is not defined")

    def register_experiment(self, timeline: str, experiment: ExperimentDefinition):
        if timeline not in self.timelines:
            raise ValueError(f"Timeline '{timeline}' is not defined")

        timeline_spec = self.timelines[timeline]
        if experiment.name in timeline_spec.experiments:
            raise ValueError(f"Experiment '{experiment.name}' already exists in timeline '{timeline}'")

        self.ensure_pipeline(experiment.pipeline)
        self.ensure_model(experiment.model)

        timeline_spec.experiments[experiment.name] = experiment
        self.experiments_index[(timeline, experiment.name)] = experiment

    def create_timeline(self, name: str, description: Optional[str], parent: Optional[str] = None):
        if name in self.timelines:
            raise ValueError(f"Timeline '{name}' already exists")

        source_parent = parent or self.current_timeline
        if source_parent not in self.timelines:
            raise ValueError(f"Parent timeline '{source_parent}' does not exist")

        self.timelines[name] = TimelineSpec(name=name, description=description, parent=source_parent)

    def record_merge(self, statement: MergeStatement):
        if statement.source_timeline not in self.timelines:
            raise ValueError(f"Cannot merge from unknown timeline '{statement.source_timeline}'")
        if statement.target_timeline not in self.timelines:
            raise ValueError(f"Cannot merge into unknown timeline '{statement.target_timeline}'")
        self.merges.append(statement)
