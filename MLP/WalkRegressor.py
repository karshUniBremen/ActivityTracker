from sklearn.metrics import confusion_matrix, accuracy_score, classification_report
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier, MLPRegressor
from window_slider import Slider
from Tools.Filters.FirFilter import FirFilter
import statistics
from sklearn import preprocessing
from scipy.fft import rfft, ifft, fftfreq
import matplotlib.pyplot as plt

WINDOW_SIZE = 100
OVERLAP_SIZE = 25
SAMPLE_FREQ = 225

def extract_gnd(in_data):
    return float(statistics.mean( data=in_data ))

def sliding_window_preprocessor(filename, target_value, window_size, overlap_size):
    dataframe = pd.read_csv( filename )
    pre_process_result = []

    # get accelerometer data and filter it first
    fir = FirFilter( dataframe, sample_rate_hz=SAMPLE_FREQ, cutoff_freq_hz=5 )
    fil_accx, raw_accx, timestamp_accx = fir.filter( signal_param="accx_g" )
    fil_accy, raw_accy, timestamp_accy = fir.filter( signal_param="accy_g" )
    fil_accz, raw_accz, timestamp_accz = fir.filter( signal_param="accz_g" )
    fil_gnd, raw_gnd, timestamp_gnd = fir.filter( signal_param="groundVelocity" )

    # get features using sliding window
    slider_accx = Slider( window_size, overlap_size )
    slider_accx.fit( fil_accx )

    slider_accy = Slider( window_size, overlap_size )
    slider_accy.fit( fil_accy )

    slider_accz = Slider( window_size, overlap_size )
    slider_accz.fit( fil_accz )

    slider_gnd = Slider( window_size, overlap_size )
    slider_gnd.fit( fil_gnd )

    while True:
        window_data_accx = slider_accx.slide()
        window_data_accy = slider_accy.slide()
        window_data_accz = slider_accz.slide()
        window_data_gnd = slider_gnd.slide()
        feature_x = extract_features( window_data_accx )
        feature_y = extract_features( window_data_accy )
        feature_z = extract_features( window_data_accz )
        t_value = extract_gnd( window_data_gnd )
        pre_process_result.append( {
            'accx_mean': feature_x['mean'],
            'accx_var': feature_x['var'],
            'accx_sd': feature_x['sd'],
            'accx_25': feature_x['per_25'],
            'accx_75': feature_x['per_75'],
            'accx_freq1': feature_x['freq1'],
            'accx_freq2': feature_x['freq2'],
            'accx_freq3': feature_x['freq3'],
            'accx_freq4': feature_x['freq4'],
            'accx_freq5': feature_x['freq5'],
            'accy_mean': feature_y['mean'],
            'accy_var': feature_y['var'],
            'accy_sd': feature_y['sd'],
            'accy_25': feature_y['per_25'],
            'accy_75': feature_y['per_75'],
            'accy_freq1': feature_y['freq1'],
            'accy_freq2': feature_y['freq2'],
            'accy_freq3': feature_y['freq3'],
            'accy_freq4': feature_y['freq4'],
            'accy_freq5': feature_y['freq5'],
            'accz_mean': feature_z['mean'],
            'accz_var': feature_z['var'],
            'accz_sd': feature_z['sd'],
            'accz_25': feature_z['per_25'],
            'accz_75': feature_z['per_75'],
            'accz_freq1': feature_z['freq1'],
            'accz_freq2': feature_z['freq2'],
            'accz_freq3': feature_z['freq3'],
            'accz_freq4': feature_z['freq4'],
            'accz_freq5': feature_z['freq5'],
            'target': t_value
        } )
        if slider_accx.reached_end_of_list(): break
    return pd.DataFrame( pre_process_result )


def extract_features(dataset):
    fft_mag = rfft( dataset )
    fft_mag = abs( fft_mag )
    fft_freq_bin = fftfreq( WINDOW_SIZE, 1 / 10 )[0:(int)( WINDOW_SIZE / 2 )]
    frequency_resp = dict( zip( fft_freq_bin, fft_mag ) )
    sorted_frequency_resp = {k: v for k, v in sorted( frequency_resp.items(), key=lambda item: item[1], reverse=True )[:5]}
    dominating_freq = list( sorted_frequency_resp.keys() )
    mean = statistics.mean( data=dataset )
    var = statistics.variance( data=dataset )
    sd = statistics.stdev( data=dataset )
    freq1 = dominating_freq[0]
    freq2 = dominating_freq[1]
    freq3 = dominating_freq[2]
    freq4 = dominating_freq[3]
    freq5 = dominating_freq[4]
    per_25 = np.percentile( dataset, 25 )
    per_75 = np.percentile( dataset, 75 )
    res = {"mean": mean,
           "var": var,
           "sd": sd,
           "per_25": per_25,
           "per_75": per_75,
           "freq1": freq1,
           "freq2": freq2,
           "freq3": freq3,
           "freq4": freq4,
           "freq5": freq5,
           }
    return res

def regressor(x,y):
    x_train, x_test, y_train, y_test = train_test_split( x, y, test_size=0.25, random_state=27 )
    mlp = MLPRegressor(hidden_layer_sizes=(8,8,8), activation='relu', solver='adam', max_iter=1000, verbose=10)
    mlp.fit(x_train,y_train)

    predict_train = mlp.predict(x_train)
    predict_test = mlp.predict(x_test)
    print(mlp.score(x_test,y_test))
    diff_vel = np.zeros(len(predict_test))
    diff_vel = y_test - predict_test
    print(diff_vel)
    # fig = plt.figure()
    # ax1 = fig.add_subplot(111)
    # ax1.plot(range(0,len(y_test)), y_test, 'b--', label='real')
    # ax1.plot(range(0,len(predict_test)),predict_test,'r--', label='NN Prediction')
    # plt.show()
    fig, ax = plt.subplots( 2, 1 )
    ax[0].plot( range( 0, len( y_test ) ), y_test, 'b--', label='real' )
    ax[1].plot( range( 0, len( predict_test ) ), predict_test, 'r--', label='NN Prediction' )
    plt.show()

if __name__ == '__main__':
    she_slow_walk_df = sliding_window_preprocessor( filename='../DataSet/Test4/she/she_slow_walk_19_dec_2020.csv', target_value='walk', window_size=WINDOW_SIZE, overlap_size=OVERLAP_SIZE )
    she_norm_walk_df = sliding_window_preprocessor( filename='../DataSet/Test4/she/she_norm_walk_19_dec_2020.csv', target_value='walk', window_size=WINDOW_SIZE, overlap_size=OVERLAP_SIZE )
    she_fast_walk_df = sliding_window_preprocessor( filename='../DataSet/Test4/she/she_fast_walk_19_dec_2020.csv', target_value='walk', window_size=WINDOW_SIZE, overlap_size=OVERLAP_SIZE )
    she_jog_walk_df = sliding_window_preprocessor( filename='../DataSet/Test4/she/she_jog_19_dec_2020.csv', target_value='run', window_size=WINDOW_SIZE, overlap_size=OVERLAP_SIZE )
    she_run_walk_df = sliding_window_preprocessor( filename='../DataSet/Test4/she/she_run_19_dec_2020.csv', target_value='run', window_size=WINDOW_SIZE, overlap_size=OVERLAP_SIZE )
    she_standing_df = sliding_window_preprocessor( filename='../DataSet/Test4/she/she_stand_19_dec_2020.csv', target_value='stand', window_size=WINDOW_SIZE, overlap_size=OVERLAP_SIZE )
    shan_slow_walk_df = sliding_window_preprocessor( filename='../DataSet/Test4/shan/shan_slow_walk_19_dec_2020.csv', target_value='walk', window_size=WINDOW_SIZE, overlap_size=OVERLAP_SIZE )
    shan_norm_walk_df = sliding_window_preprocessor( filename='../DataSet/Test4/shan/shan_norm_walk_19_dec_2020.csv', target_value='walk', window_size=WINDOW_SIZE, overlap_size=OVERLAP_SIZE )
    shan_fast_walk_df = sliding_window_preprocessor( filename='../DataSet/Test4/shan/shan_fast_walk_19_dec_2020.csv', target_value='walk', window_size=WINDOW_SIZE, overlap_size=OVERLAP_SIZE )
    shan_jog_walk_df = sliding_window_preprocessor( filename='../DataSet/Test4/shan/shan_jog_19_dec_2020.csv', target_value='run', window_size=WINDOW_SIZE, overlap_size=OVERLAP_SIZE )
    shan_run_walk_df = sliding_window_preprocessor( filename='../DataSet/Test4/shan/shan_run_19_dec_2020.csv', target_value='run', window_size=WINDOW_SIZE, overlap_size=OVERLAP_SIZE )
    shan_standing_df = sliding_window_preprocessor( filename='../DataSet/Test4/shan/shan_stand_19_dec_2020.csv', target_value='stand', window_size=WINDOW_SIZE, overlap_size=OVERLAP_SIZE )

    # create a large dataframe
    feature_vector = pd.concat( [she_norm_walk_df, she_standing_df, she_run_walk_df, she_jog_walk_df, she_slow_walk_df, she_fast_walk_df,
                                 shan_fast_walk_df, shan_slow_walk_df, shan_norm_walk_df, shan_run_walk_df, shan_standing_df, shan_jog_walk_df] )
    feature_vector.reset_index( drop=True, inplace=True )

    # normalize the data
    normalizer = preprocessing.Normalizer().fit( feature_vector.drop( ['target'], axis=1 ) )
    input_vector_norm = normalizer.transform( feature_vector.drop( ['target'], axis=1 ) )

    output_vector_norm = feature_vector['target']/feature_vector['target'].max()

    regressor( input_vector_norm, output_vector_norm )
