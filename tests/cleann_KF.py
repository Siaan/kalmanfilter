#flake8: noqa
#! /usr/bin/env python
import sys
from pandas.core.common import flatten
import numpy as np
from filterpy.kalman import KalmanFilter
import matplotlib.pyplot as plt
from filterpy.common import Q_discrete_white_noise
from filterpy.stats import plot_covariance_ellipse  # noqa: F401
#import process_files


def preprocess( num_measured,measured_var, covar, process_model, white_noise_var, dt,sensor_covar, measurement_function,B=0, U=0):
    '''
    :param num_measured: size of measurement vector.
           For example: if there is only one sensor that measures position x then num_measured = 1 # noqa: E501, W291
    :param measured_var: Mean state variables vector
           For example: State variables can be either observed (directly measured by a sensor) or # noqa: E501
           hidden variables (inferred from observed variables). For a sensor that measures the x (position - e.x 10) # noqa: E501
           of a car, we can infer the velocity (dx - e.x 4.5)
           Therefore mean state variable vector is [10, 4.5].T for a 2d case
           measured_var = (10,4.5) # noqa: W291
    :param covar: Covariance matrix of all state variables
           For example: if the variance of x = 500 and dx = 49 and the correlation is unknown # noqa: E501
           covar = ((500,0),(0,49))
    :param process_model: Transition matrix for process
           For example: The relationship between x and dx is: x'  = 1* x + (dt) dx  where dt = 0.1 # noqa: E501
                                                              dx' = 0* x + (1)  dx (for our purposes)
           Then process_model= ((1, 0.1), (0, 1))
    :param white_noise_var: Variance of noise in process (float)
    :param dt: time step (in seconds)
    :param sensor_covar: Variance in sensor measurement (noise)
           For example: If only one sensor is used to measure x
           sensor_covar = (5)
           If two sensors are used to measure x and dx
           sensor_covar = (5,0),(0,2) etc
    :param measurement_function: Converts state to measurement
           For example: if the measurement is x from the sensor but the state variable is x and dx
           then in matrix form : x - [1 0] [x, dx] = x - x
           Measurement_function = (1,0)
    :param B: Control input matrix
    :param U: Control input
    :return: all the variables above in np.array form
    '''

    dim_z = int(num_measured)
    X = np.array([measured_var])
    # fix X
    X = np.array([[10], [4.5]])
    P = np.array(eval(covar))
    print(P)
    print('===========')
    print(type(eval(covar)))
    A = np.array(eval(process_model))
    Q = Q_discrete_white_noise(
        dim=X.shape[0],
        dt=dt,
        var=white_noise_var)  # dim = shape of X?
    B = B
    U = U
    R = np.array([[int(sensor_covar)]])
    H = np.array([eval(measurement_function)])
    print('x', X)
    print(P)
    print(A)
    print(R)
    print('h', H)
    print(type(A))
    return (dim_z, X, P, A, Q, dt, R, H, B, U)


def create_kf_and_assign_predict_update(dim_z, X, P, A, Q, dt, R, H, B, U):
    '''
    :param configs tuple: all the values to define the kalman filter
    :return: Kalman Filter
    '''

    kf = KalmanFilter(dim_x=X.shape[0], dim_z=dim_z)
    kf.x = X
    kf.P = P
    kf.F = A
    print('=======================')
    kf.Q = Q
    kf.B = B
    kf.U = U
    kf.R = R
    kf.H = H
    return kf


# data = zedd
def run_kf( data, dim_of_measurements,measured_var,covar, process_model,white_noise_var, dt,sensor_covar,measurement_function):
    '''
    This runs the kalman filter on noisy data entered
    :return: Filtered data, covariances and kalman filter used
    '''
    xs, cv = [], []
    dim_z, X, P, A, Q, dt, R, H, B, U = preprocess(num_measured=dim_of_measurements, measured_var=measured_var, covar=covar, process_model=process_model, white_noise_var=white_noise_var, dt=dt, 
                                                   sensor_covar=sensor_covar, measurement_function=measurement_function)
    kf = create_kf_and_assign_predict_update(dim_z, X, P, A, Q, dt, R, H, B, U)

    for i in data:
        kf.predict()
        kf.update(i)

        xs.append(kf.x)
        cv.append(kf.P)

    xs, cv = np.array(xs), np.array(cv)
    return xs, cv, kf


def run_smoother(kf, xs, ps):
    '''

    :param kf: Kalman filter used in filter step
    :param xs: filtered data
    :param ps: covariances
    :return: x = smoothed data, P = covariances
    '''
    x, P, K, Pp = kf.rts_smoother(Xs=xs, Ps=ps)
    return x, P


def visualise(x, y, x_messy, x_real=None):
    '''

    :param x: filterd/smoothed data
    :param y: covariances
    :param x_real: real data
    :param x_messy: raw measurements from sensors
    :return: plot comparing raw data and smooth/filtered data
    '''
    plt.figure(figsize=(10, 10))
    plt.plot(range(1, len(x) + 1), x[:, 0], c='r', label='Smoothed data')
    plt.plot(range( 1, len(x_messy) + 1), x_messy, '--o', c='g',label='Noisy Measurement')
    if x_real.all() is not None:
        plt.plot(range( 1, len(x_real) + 1),x_real,'--o',c='royalblue',label='True position')
    # plt.plot(range(1, len(x)+1), cv, c='r', label='Smoothed data')

    plt.legend()
    plt.title('RTS Smoother')
    plt.show()
    return
'''

if __name__ == '__main__':
    configname = sys.argv[1]
    configstore = sys.argv[2]
    input_file = sys.argv[3]
    output_loc = sys.argv[4]

    print(input_file)
    print('==========INPUT FILE====================')

    dim_of_measurements, measured_var, covar, process_model, \
        white_noise_var, dt, sensor_covar, \
        measurement_function = process_files.process_parameters(configname)

    zedd = process_files.process_data_file(input_file)
    print('Fix input file')
    print(zedd)
    print('original input')

    xs, cv, kf = run_kf(data=zedd, dim_of_measurements=dim_of_measurements, measured_var=(measured_var), covar=(covar),  # noqa: E501
                        process_model=(process_model), white_noise_var=white_noise_var, dt=dt, sensor_covar=(sensor_covar),  # noqa: E501
                        measurement_function=(measurement_function))

    x, p = run_smoother(kf, xs, cv)

    final_x = []
    for i in x:
        final_x.append(list(flatten(i)))

    print(final_x)
    print('type: ', type(final_x))
    print('FINAL_X', final_x[0])
    print(final_x[0][0])
    print(type(p))
    # print('==============+P============', p[0]) # noqa: E501

    process_files.process_output(final_x, p, output_loc)

    # Kalman.visualise(x, p, zedd, real)
'''
