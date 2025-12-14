import tempfile
import unittest

from src.monitoring.telemetry_schema import TelemetryStore
from src.pipelines.examples.sample_pipeline import SamplePipeline

class TestSamplePipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        telemetry_store = TelemetryStore(base_path=self.temp_dir.name, filename="pipeline_runs.csv")
        self.pipeline = SamplePipeline(telemetry_store=telemetry_store)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_initialization(self):
        self.assertIsNotNone(self.pipeline)
        self.assertEqual(self.pipeline.name, "Sample Pipeline")

    def test_pipeline_execution(self):
        result = self.pipeline.execute()
        self.assertTrue(result)
        self.assertEqual(self.pipeline.status, "completed")

    def test_pipeline_data_output(self):
        self.pipeline.execute()
        output = self.pipeline.get_output()
        self.assertIsInstance(output, list)
        self.assertGreater(len(output), 0)

if __name__ == '__main__':
    unittest.main()