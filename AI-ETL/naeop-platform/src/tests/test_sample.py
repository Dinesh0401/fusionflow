import unittest
from src.pipelines.examples.sample_pipeline import SamplePipeline

class TestSamplePipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = SamplePipeline()

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