import unittest
from src.controllers.data_controller import DataController

class TestDataController(unittest.TestCase):
    def setUp(self):
        self.controller = DataController()

    def test_receive_data_valid(self):
        json_data = {"key": "value"}
        response = self.controller.receive_data(json_data)
        self.assertEqual(response['status'], 'success')
        self.assertEqual(response['data'], json_data)

    def test_receive_data_invalid(self):
        json_data = {"invalid_key": "value"}
        response = self.controller.receive_data(json_data)
        self.assertEqual(response['status'], 'error')
        self.assertIn('message', response)