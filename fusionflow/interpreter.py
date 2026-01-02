"""Interpreter for FusionFlow language"""

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from .ast_nodes import *
from .runtime import Runtime 

class Interpreter:
    def __init__(self, runtime=None):
        self.runtime = runtime or Runtime()
        self.current_pipeline_data = None
    
    def execute(self, ast):
        """Execute an AST"""
        if isinstance(ast, Program):
            for statement in ast.statements:
                self.execute_statement(statement)
        else:
            self.execute_statement(ast)
    
    def execute_statement(self, stmt):
        """Execute a single statement"""
        if isinstance(stmt, DatasetDeclaration):
            self.execute_dataset_declaration(stmt)
        elif isinstance(stmt, PipelineDefinition):
            self.execute_pipeline_definition(stmt)
        elif isinstance(stmt, ExperimentDefinition):
            self.execute_experiment_definition(stmt)
        elif isinstance(stmt, PrintStatement):
            self.execute_print_statement(stmt)
        elif isinstance(stmt, CheckpointStatement):
            self.execute_checkpoint_statement(stmt)
        elif isinstance(stmt, TimelineStatement):
            self.execute_timeline_statement(stmt)
        elif isinstance(stmt, MergeStatement):
            self.execute_merge_statement(stmt)
        elif isinstance(stmt, UndoStatement):
            self.execute_undo_statement(stmt)
    
    def execute_dataset_declaration(self, stmt):
        """Load a dataset from file"""
        path = stmt.path
        
        if path.endswith('.csv'):
            data = pd.read_csv(path)
        elif path.endswith('.parquet'):
            data = pd.read_parquet(path)
        else:
            raise ValueError(f"Unsupported file format: {path}")
        
        self.runtime.register_dataset(stmt.name, data)
    
    def execute_pipeline_definition(self, stmt):
        """Execute pipeline definition"""
        self.runtime.register_pipeline(stmt.name, stmt)
        
        # Execute pipeline immediately
        data = None
        features = []
        target = None
        train_percent = 0.8
        
        for clause in stmt.body:
            if isinstance(clause, FromClause):
                data = self.runtime.get_dataset(clause.dataset_name)
                if data is None:
                    raise ValueError(f"Dataset '{clause.dataset_name}' not found")
                data = data.copy()
            
            elif isinstance(clause, WhereClause):
                condition = self.evaluate_expression(clause.condition, data)
                data = data[condition]
            
            elif isinstance(clause, JoinClause):
                join_data = self.runtime.get_dataset(clause.dataset_name)
                # Simple join implementation
                data = pd.merge(data, join_data, how='inner')
            
            elif isinstance(clause, DeriveClause):
                data[clause.variable] = self.evaluate_expression(clause.expression, data)
            
            elif isinstance(clause, FeaturesClause):
                features = clause.feature_list
            
            elif isinstance(clause, TargetClause):
                target = clause.target_name
            
            elif isinstance(clause, SplitClause):
                train_percent = clause.train_percent / 100.0
        
        # Store processed pipeline data
        pipeline_result = {
            'data': data,
            'features': features,
            'target': target,
            'train_percent': train_percent
        }
        self.runtime.set_state(f'pipeline_{stmt.name}', pipeline_result)
    
    def execute_experiment_definition(self, stmt):
        """Execute experiment (train model)"""
        # Get pipeline data
        pipeline_data = self.runtime.get_state().get(f'pipeline_{stmt.pipeline_name}')
        if not pipeline_data:
            raise ValueError(f"Pipeline '{stmt.pipeline_name}' not found or not executed")
        
        data = pipeline_data['data']
        features = pipeline_data['features']
        target = pipeline_data['target']
        train_percent = pipeline_data['train_percent']
        
        # Prepare data
        X = data[features]
        y = data[target]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, train_size=train_percent, random_state=42
        )
        
        # Train model
        if stmt.model_type.lower() == 'random_forest':
            model = RandomForestClassifier(random_state=42)
        elif stmt.model_type.lower() == 'logistic_regression':
            model = LogisticRegression(random_state=42, max_iter=1000)
        else:
            raise ValueError(f"Unknown model type: {stmt.model_type}")
        
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
        
        metrics_results = {}
        for metric in stmt.metrics:
            if metric.lower() == 'accuracy':
                metrics_results['accuracy'] = accuracy_score(y_test, y_pred)
            elif metric.lower() == 'f1':
                metrics_results['f1'] = f1_score(y_test, y_pred, average='weighted')
            elif metric.lower() == 'precision':
                metrics_results['precision'] = precision_score(y_test, y_pred, average='weighted')
            elif metric.lower() == 'recall':
                metrics_results['recall'] = recall_score(y_test, y_pred, average='weighted')
            elif metric.lower() == 'auc' and y_pred_proba is not None:
                try:
                    metrics_results['auc'] = roc_auc_score(y_test, y_pred_proba)
                except:
                    metrics_results['auc'] = None
        
        experiment_result = {
            'model': model,
            'metrics': metrics_results,
            'X_test': X_test,
            'y_test': y_test,
            'y_pred': y_pred
        }
        
        self.runtime.register_experiment(stmt.name, experiment_result)
    
    def execute_print_statement(self, stmt):
        """Print statement execution"""
        if stmt.what.lower() == 'metrics':
            experiment = self.runtime.get_experiment(stmt.of)
            if experiment:
                print(f"\n=== Metrics for {stmt.of} ===")
                for metric, value in experiment['metrics'].items():
                    if value is not None:
                        print(f"{metric}: {value:.4f}")
                    else:
                        print(f"{metric}: N/A")
            else:
                print(f"Experiment '{stmt.of}' not found")
    
    def execute_checkpoint_statement(self, stmt):
        """Create checkpoint"""
        self.runtime.create_checkpoint(stmt.name)
    
    def execute_timeline_statement(self, stmt):
        """Execute timeline block"""
        # Save current timeline
        previous_timeline = self.runtime.current_timeline
        
        # Create new timeline
        self.runtime.create_timeline(stmt.name)
        
        # Execute timeline body
        for statement in stmt.body:
            self.execute_statement(statement)
        
        # Return to previous timeline
        self.runtime.current_timeline = previous_timeline
    
    def execute_merge_statement(self, stmt):
        """Merge timelines"""
        self.runtime.merge_timeline(stmt.source_timeline, stmt.target_timeline)
    
    def execute_undo_statement(self, stmt):
        """Restore checkpoint"""
        self.runtime.restore_checkpoint(stmt.checkpoint_name)
    
    def evaluate_expression(self, expr, data):
        """Evaluate an expression"""
        if isinstance(expr, Literal):
            return expr.value
        
        elif isinstance(expr, Identifier):
            if expr.name in data.columns:
                return data[expr.name]
            return expr.name
        
        elif isinstance(expr, MemberAccess):
            obj = self.evaluate_expression(expr.object, data)
            # Simple member access for dataset.column
            if isinstance(obj, str) and obj in self.runtime.datasets:
                dataset = self.runtime.datasets[obj]
                return dataset[expr.member]
            return obj
        
        elif isinstance(expr, BinaryOp):
            left = self.evaluate_expression(expr.left, data)
            right = self.evaluate_expression(expr.right, data)
            
            if expr.operator == '+':
                return left + right
            elif expr.operator == '-':
                return left - right
            elif expr.operator == '*':
                return left * right
            elif expr.operator == '/':
                return left / right
            elif expr.operator == '==':
                return left == right
            elif expr.operator == '!=':
                return left != right
            elif expr.operator == '<':
                return left < right
            elif expr.operator == '>':
                return left > right
            elif expr.operator == '<=':
                return left <= right
            elif expr.operator == '>=':
                return left >= right
            elif expr.operator == 'and':
                return left & right
            elif expr.operator == 'or':
                return left | right
        
        elif isinstance(expr, UnaryOp):
            operand = self.evaluate_expression(expr.operand, data)
            if expr.operator == 'not':
                return ~operand
        
        return None
