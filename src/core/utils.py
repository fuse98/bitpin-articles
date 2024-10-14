import math
from typing import Tuple, List


def calculate_zscore(mean, variance, data_point):
    std_dev = math.sqrt(variance)
    z_score = (data_point - mean) / std_dev

    return z_score


def calculate_normal_distribution_pdf(mean, variance, data_point):
    # using PDF formula for normal distribution
    denom = (2 * math.pi * variance)**.5
    num = math.exp(-(float(data_point) - float(mean))**2 / (2 * variance))
    return num/denom


def calculate_new_normal_dist_info_with_data_update(
    mean: float,
    mean_diff_square_sum: float,
    data_count: int,
    new_data_point: int,
    old_data_point:int
) -> Tuple[float, float]:
    '''
    Calculates new mean and new mean_diff_square_sum.
    return new_mean, new_mean_diff_square_sum
    '''
    new_mean = ((mean * data_count) + (new_data_point - old_data_point))/data_count

    M2_adjustment_new = (new_data_point - mean) * (new_data_point - new_mean)
    M2_adjustment_old = (old_data_point - mean) * (old_data_point - new_mean)
    new_mean_diff_square_sum = mean_diff_square_sum + M2_adjustment_new - M2_adjustment_old
    return (new_mean, new_mean_diff_square_sum)


def calculate_new_normal_dist_info_with_new_data_points(
    mean: float,
    mean_diff_square_sum: float,
    data_count: int,
    new_data_points: List[int],
) -> Tuple[float, float, int]:
    '''
    Calculates new mean, new mean_diff_square_sum and new data count
    return new_mean, new_mean_diff_square_sum, new_data_count
    '''
    new_data_count = data_count + len(new_data_points)
    delta = [new_data_point - mean for new_data_point in new_data_points]
    new_mean = mean + sum(delta) / new_data_count
    delta2 = [new_data_point - new_mean for new_data_point in new_data_points]
    new_mean_diff_square_sum = mean_diff_square_sum + sum(d * d2 for d, d2 in zip(delta, delta2))

    return (new_mean, new_mean_diff_square_sum, new_data_count)
