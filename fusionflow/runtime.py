"""Runtime state management with temporal branching support"""

import copy
from typing import Dict, Any, List

class Runtime:
    def __init__(self):
        self.datasets = {}
        self.pipelines = {}
        self.experiments = {}
        self.checkpoints = {}
        self.timelines = {'main': {}}
        self.current_timeline = 'main'
    
    def get_state(self):
        """Get current timeline state"""
        return self.timelines[self.current_timeline]
    
    def set_state(self, key, value):
        """Set value in current timeline"""
        self.timelines[self.current_timeline][key] = value
    
    def register_dataset(self, name, data):
        """Register a dataset"""
        self.datasets[name] = data
    
    def get_dataset(self, name):
        """Get a registered dataset"""
        return self.datasets.get(name)
    
    def register_pipeline(self, name, pipeline_def):
        """Register a pipeline definition"""
        self.pipelines[name] = pipeline_def
    
    def get_pipeline(self, name):
        """Get a pipeline definition"""
        return self.pipelines.get(name)
    
    def register_experiment(self, name, experiment_data):
        """Register experiment results"""
        self.experiments[name] = experiment_data
    
    def get_experiment(self, name):
        """Get experiment results"""
        return self.experiments.get(name)
    
    def create_checkpoint(self, name):
        """Save current state as a checkpoint"""
        self.checkpoints[name] = {
            'datasets': copy.deepcopy(self.datasets),
            'pipelines': copy.deepcopy(self.pipelines),
            'experiments': copy.deepcopy(self.experiments),
            'timeline': self.current_timeline
        }
    
    def restore_checkpoint(self, name):
        """Restore state from a checkpoint"""
        if name not in self.checkpoints:
            raise ValueError(f"Checkpoint '{name}' not found")
        
        checkpoint = self.checkpoints[name]
        self.datasets = copy.deepcopy(checkpoint['datasets'])
        self.pipelines = copy.deepcopy(checkpoint['pipelines'])
        self.experiments = copy.deepcopy(checkpoint['experiments'])
        self.current_timeline = checkpoint['timeline']
    
    def create_timeline(self, name):
        """Create a new isolated timeline"""
        if name in self.timelines:
            raise ValueError(f"Timeline '{name}' already exists")
        
        # Copy current state to new timeline
        self.timelines[name] = copy.deepcopy(self.get_state())
        self.current_timeline = name
    
    def merge_timeline(self, source, target):
        """Merge source timeline into target timeline"""
        if source not in self.timelines:
            raise ValueError(f"Source timeline '{source}' not found")
        if target not in self.timelines:
            raise ValueError(f"Target timeline '{target}' not found")
        
        # Simple merge: target gets source's data
        self.timelines[target].update(copy.deepcopy(self.timelines[source]))
        self.current_timeline = target
