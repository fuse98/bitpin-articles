import math

def calculate_zscore(mean, variance, data_point):
    std_dev = math.sqrt(variance)    
    z_score = (data_point - mean) / std_dev

    return z_score

def calculate_normal_distribution_pdf(mean, variance, data_point):
    # using PDF formula for normal distribution
    denom = (2 * math.pi * variance)**.5
    num = math.exp(-(float(data_point) - float(mean))**2 / (2 * variance))
    return num/denom
