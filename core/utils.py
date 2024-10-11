import math

def calculate_zscore(mean, variance, data_point):
    std_dev = math.sqrt(variance)    
    z_score = (data_point - mean) / std_dev

    return z_score
