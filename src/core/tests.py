from django.test import TestCase
from core.utils import (
    calculate_new_normal_dist_info_with_data_update,
    calculate_new_normal_dist_info_with_new_data_points,
)


class TestUtils(TestCase):

    def setUp(self):
        self.initila_values = [1, 4, 5, 2, 3, 5, 1, 4, 2, 2, 3, 3, 5, 0, 4, 4, 3, 2, 1, 0]
        self.mean = self.calc_mean(self.initila_values)
        self.mean_diff_square_sum = self.calc_mean_diff_square_sum(self.initila_values)

    def calc_mean(self, values):
        return sum(values) / len(values)

    def calc_mean_diff_square_sum(self, values):
        mean = self.calc_mean(values)
        mean_diff_squares_sum = 0
        for v in values:
            mean_diff_squares_sum += (mean - v)**2
        return mean_diff_squares_sum

    def test_calculate_new_normal_dist_info_with_new_data_points_should_return_correct_values(self):
        new_values = [4, 3, 4, 0, 2, 1]
        new_mean, new_mean_diff_square_sum, new_count = calculate_new_normal_dist_info_with_new_data_points(
            self.mean,
            self.mean_diff_square_sum,
            len(self.initila_values),
            new_values,
        )
        all_values = self.initila_values + new_values
        expected_mean = self.calc_mean(all_values)
        expected_mean_diff_square_sum = self.calc_mean_diff_square_sum(all_values)
        expected_count = len(all_values)
        self.assertEqual(new_mean, expected_mean)
        self.assertAlmostEqual(new_mean_diff_square_sum, expected_mean_diff_square_sum, 3)
        self.assertEqual(new_count, expected_count)

    def test_calculate_new_normal_dist_info_with_data_update_should_return_correct_values(self):
        old_value = 0
        new_value = 3
        new_mean, new_mean_diff_square_sum = calculate_new_normal_dist_info_with_data_update(
            self.mean,
            self.mean_diff_square_sum,
            len(self.initila_values),
            new_value,
            old_value
        )
        new_values = self.initila_values
        for i in range(len(new_values)):
            if new_values[i] == old_value:
                new_values[i] = new_value
                break

        expected_mean = self.calc_mean(new_values)
        expected_mean_diff_square_sum = self.calc_mean_diff_square_sum(new_values)
        self.assertEqual(new_mean, expected_mean)
        self.assertAlmostEqual(new_mean_diff_square_sum, expected_mean_diff_square_sum, 3)
