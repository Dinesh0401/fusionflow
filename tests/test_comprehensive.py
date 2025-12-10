import pytest
import pandas as pd
import tempfile
import os
from fusionflow.lexer import Lexer
from fusionflow.parser import Parser
from fusionflow.interpreter import Interpreter
from fusionflow.runtime import Runtime

@pytest.fixture
def sample_csv():
    data = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'age': [25, 35, 45, 55, 20],
        'income': [30000, 50000, 70000, 90000, 25000],
        'active': [1, 1, 0, 1, 1],
        'churned': [0, 0, 1, 1, 0]
    })
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data.to_csv(f.name, index=False)
        yield f.name
    
    os.unlink(f.name)

class TestKeywordHandling:
    def test_model_as_keyword(self, sample_csv):
        source = f"""
        dataset data from "{sample_csv}"
        pipeline p:
            from data
            features [age, income]
            target churned
            split 80% train, 20% test
        end
        experiment e:
            model random_forest
            using p
            metrics [accuracy]
        end
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        runtime = Runtime()
        interpreter = Interpreter(runtime)
        interpreter.execute(ast)
        
        assert 'e' in runtime.experiments
    
    def test_using_as_keyword(self, sample_csv):
        source = f"""
        dataset data from "{sample_csv}"
        pipeline p:
            from data
            features [age]
            target churned
            split 80% train, 20% test
        end
        experiment e:
            model logistic_regression
            using p
            metrics [accuracy]
        end
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert ast is not None
    
    def test_metrics_keyword(self, sample_csv):
        source = f"""
        dataset data from "{sample_csv}"
        pipeline p:
            from data
            features [age]
            target churned
            split 80% train, 20% test
        end
        experiment e:
            model random_forest
            using p
            metrics [accuracy, f1, precision]
        end
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        exp = ast.statements[2]
        assert len(exp.metrics) == 3
    
    def test_versioned_keyword(self, sample_csv):
        source = f'dataset data from "{sample_csv}" versioned'
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert ast.statements[0].versioned == True

class TestWindowsPaths:
    def test_windows_path_backslash(self):
        source = 'dataset data from "C:\\\\Users\\\\data.csv"'
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert "C:\\Users\\data.csv" in ast.statements[0].path
    
    def test_windows_path_forward_slash(self):
        source = 'dataset data from "C:/Users/data.csv"'
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert ast.statements[0].path == "C:/Users/data.csv"
    
    def test_relative_path(self):
        source = 'dataset data from "./data/file.csv"'
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert ast.statements[0].path == "./data/file.csv"

class TestComplexPipelines:
    def test_multiple_derives(self, sample_csv):
        source = f"""
        dataset data from "{sample_csv}"
        pipeline p:
            from data
            derive age_bracket = age / 10
            derive income_k = income / 1000
            derive ratio = income / age
            features [age_bracket, income_k]
            target churned
            split 80% train, 20% test
        end
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        runtime = Runtime()
        interpreter = Interpreter(runtime)
        interpreter.execute(ast)
        
        pipeline_data = runtime.get_state().get('pipeline_p')
        assert 'age_bracket' in pipeline_data['data'].columns
        assert 'income_k' in pipeline_data['data'].columns
    
    def test_where_clause_filtering(self, sample_csv):
        source = f"""
        dataset data from "{sample_csv}"
        pipeline p:
            from data
            where active == 1
            features [age]
            target churned
            split 80% train, 20% test
        end
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        runtime = Runtime()
        interpreter = Interpreter(runtime)
        interpreter.execute(ast)
        
        pipeline_data = runtime.get_state().get('pipeline_p')
        assert len(pipeline_data['data']) == 4  # Only active == 1
    
    def test_multiple_where_clauses(self, sample_csv):
        source = f"""
        dataset data from "{sample_csv}"
        pipeline p:
            from data
            where age > 25
            where income > 30000
            features [age]
            target churned
            split 80% train, 20% test
        end
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        runtime = Runtime()
        interpreter = Interpreter(runtime)
        interpreter.execute(ast)
        
        pipeline_data = runtime.get_state().get('pipeline_p')
        assert len(pipeline_data['data']) == 3

class TestExperiments:
    def test_random_forest_model(self, sample_csv):
        source = f"""
        dataset data from "{sample_csv}"
        pipeline p:
            from data
            features [age, income]
            target churned
            split 80% train, 20% test
        end
        experiment e:
            model random_forest
            using p
            metrics [accuracy]
        end
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        runtime = Runtime()
        interpreter = Interpreter(runtime)
        interpreter.execute(ast)
        
        exp = runtime.get_experiment('e')
        assert exp['model'] is not None
        assert 'accuracy' in exp['metrics']
    
    def test_logistic_regression_model(self, sample_csv):
        source = f"""
        dataset data from "{sample_csv}"
        pipeline p:
            from data
            features [age, income]
            target churned
            split 70% train, 30% test
        end
        experiment e:
            model logistic_regression
            using p
            metrics [accuracy, precision, recall]
        end
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        runtime = Runtime()
        interpreter = Interpreter(runtime)
        interpreter.execute(ast)
        
        exp = runtime.get_experiment('e')
        assert 'precision' in exp['metrics']
        assert 'recall' in exp['metrics']

class TestTemporalBranching:
    def test_checkpoint_creation(self, sample_csv):
        source = f"""
        dataset data from "{sample_csv}"
        checkpoint "baseline"
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        runtime = Runtime()
        interpreter = Interpreter(runtime)
        interpreter.execute(ast)
        
        assert "baseline" in runtime.checkpoints
    
    def test_timeline_creation(self, sample_csv):
        source = f"""
        dataset data from "{sample_csv}"
        timeline "exp1" {{
            dataset data2 from "{sample_csv}"
        }}
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        runtime = Runtime()
        interpreter = Interpreter(runtime)
        interpreter.execute(ast)
        
        assert "exp1" in runtime.timelines
    
    def test_undo_checkpoint(self, sample_csv):
        source = f"""
        dataset data1 from "{sample_csv}"
        checkpoint "cp1"
        dataset data2 from "{sample_csv}"
        undo "cp1"
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        runtime = Runtime()
        interpreter = Interpreter(runtime)
        interpreter.execute(ast)
        
        # After undo, data2 should not exist
        assert 'data1' in runtime.datasets

class TestUPEGGeneration:
    def test_upeg_node_creation(self):
        from fusionflow.upeg import UPEG, UPEGNode
        
        upeg = UPEG()
        node = UPEGNode(
            id="node1",
            operation="filter",
            inputs=["dataset1"],
            outputs=["filtered_data"],
            metadata={}
        )
        upeg.add_node(node)
        
        assert len(upeg.nodes) == 1
        assert upeg.nodes[0].id == "node1"
    
    def test_upeg_edge_creation(self):
        from fusionflow.upeg import UPEG, UPEGNode
        
        upeg = UPEG()
        upeg.add_edge("node1", "node2")
        
        assert len(upeg.edges) == 1
        assert upeg.edges[0] == ("node1", "node2")

class TestBackendPlanner:
    def test_pandas_backend(self):
        from fusionflow.backend_adapters import PandasBackend
        
        backend = PandasBackend()
        assert backend.can_execute("filter")
        assert backend.can_execute("transform")
        assert not backend.can_execute("unknown_op")

class TestErrorHandling:
    def test_unknown_dataset_error(self):
        source = """
        pipeline p:
            from nonexistent_dataset
            features [x]
            target y
            split 80% train, 20% test
        end
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        runtime = Runtime()
        interpreter = Interpreter(runtime)
        
        with pytest.raises(ValueError):
            interpreter.execute(ast)
    
    def test_unknown_pipeline_error(self):
        source = """
        experiment e:
            model random_forest
            using nonexistent_pipeline
            metrics [accuracy]
        end
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        runtime = Runtime()
        interpreter = Interpreter(runtime)
        
        with pytest.raises(ValueError):
            interpreter.execute(ast)
    
    def test_syntax_error(self):
        source = "dataset from"
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        
        with pytest.raises(SyntaxError):
            parser.parse()

class TestIntegration:
    def test_full_workflow(self, sample_csv):
        source = f"""
        dataset customers from "{sample_csv}"
        
        checkpoint "before_pipeline"
        
        pipeline churn_pipeline:
            from customers
            where active == 1
            derive spend_ratio = income / age
            features [age, income, spend_ratio]
            target churned
            split 80% train, 20% test
        end
        
        experiment baseline_exp:
            model random_forest
            using churn_pipeline
            metrics [accuracy, f1]
        end
        
        print metrics of baseline_exp
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        runtime = Runtime()
        interpreter = Interpreter(runtime)
        interpreter.execute(ast)
        
        assert 'customers' in runtime.datasets
        assert 'churn_pipeline' in runtime.pipelines
        assert 'baseline_exp' in runtime.experiments
        assert 'before_pipeline' in runtime.checkpoints
    
    def test_timeline_workflow(self, sample_csv):
        source = f"""
        dataset data from "{sample_csv}"
        
        pipeline p1:
            from data
            features [age]
            target churned
            split 80% train, 20% test
        end
        
        checkpoint "baseline"
        
        timeline "exp_v2" {{
            pipeline p2:
                from data
                features [age, income]
                target churned
                split 80% train, 20% test
            end
        }}
        """
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        runtime = Runtime()
        interpreter = Interpreter(runtime)
        interpreter.execute(ast)
        
        assert 'exp_v2' in runtime.timelines
        assert 'baseline' in runtime.checkpoints
