import numpy as np
from scipy import signal

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, FeatureUnion


class TwoDScaler(BaseEstimator, TransformerMixin):
    """
        Zero mean and unit variance scaler
    """

    def __init__(self):
        pass

    def fit(self, x, y=None):
        return self

    def transform(self, x):
        norm = (x - np.mean(x, axis=(2, 3), keepdims=True)) \
               / (np.std(x, axis=(2, 3), keepdims=True) + 1e-4)
        return norm


class Spectrogram(BaseEstimator, TransformerMixin):
    """
    Computes the spectrogram of specific channel
    """

    def __init__(self, channel: str, sampling_rate: int, window: int,
                 stride: int):
        self.channel = channel
        self.sampling_rate = sampling_rate
        self.window = window
        self.stride = stride

    def fit(self, x, y=None):
        return self

    def transform(self, x):
        psg = x[self.channel]
        padding = self.window // 2 - self.stride // 2
        psg = np.pad(psg, pad_width=((0, 0), (padding, padding)), mode='edge')
        f, t, sxx = signal.spectrogram(psg, fs=self.sampling_rate,
                                       nperseg=self.window,
                                       noverlap=self.window - self.stride,
                                       scaling='density', mode='psd')
        sxx = sxx[:, np.newaxis, :, :]
        return sxx


class PowerSpectralDensityMean(BaseEstimator, TransformerMixin):
    """
    Computes the mean power spectral density from a spectrogram and repeats the
     values to 'output_dim'
    """

    def __init__(self, output_dim: int):
        self.output_dim = output_dim

    def fit(self, x, y=None):
        return self

    def transform(self, x):
        psd = np.mean(x, axis=2, keepdims=True)
        rep = np.repeat(psd, self.output_dim, axis=2)
        return rep


class PowerSpectralDensitySum(BaseEstimator, TransformerMixin):
    """
    Computes the sum power spectral density from a spectrogram and repeats the
     values to 'output_dim'
    """

    def __init__(self, output_dim: int):
        self.output_dim = output_dim

    def fit(self, x, y=None):
        return self

    def transform(self, x):
        psd = np.sum(x, axis=2, keepdims=True)
        rep = np.repeat(psd, self.output_dim, axis=2)
        return rep


class CutFrequencies(BaseEstimator, TransformerMixin):
    """
    Cuts out the spectrogram between lower and upper frequency
    """

    def __init__(self, window: int, sampling_rate: int, lower: float,
                 upper: float):
        self.f = np.fft.rfftfreq(window, 1.0 / sampling_rate)
        self.lower = lower
        self.upper = upper

    def fit(self, x, y=None):
        return self

    def transform(self, x):
        cut = x[:, :,
              np.logical_and(self.f >= self.lower, self.f <= self.upper), :]
        return cut


class LogTransform(BaseEstimator, TransformerMixin):
    """
    Computes the log transform of the given features
    """

    def __init__(self):
        pass

    def fit(self, x, y=None):
        return self

    def transform(self, x):
        return np.log(x + 1e-4)


eeg_spectrogram = Pipeline([
    ('spectrogram',
     Spectrogram(channel='EEG', sampling_rate=250, window=500, stride=100)),
    ('cutter', CutFrequencies(window=500, sampling_rate=250, lower=0, upper=25)),
    ('log', LogTransform()),
    ('standard', TwoDScaler())
])

emg_psd = Pipeline([
    ('spectrogram',
     Spectrogram(channel='EMG', sampling_rate=250, window=500, stride=100)),
    (
    'cutter', CutFrequencies(window=500, sampling_rate=250, lower=0, upper=60)),
    ('psd', PowerSpectralDensityMean(output_dim=51)),
    ('log', LogTransform()),
    ('standard', TwoDScaler())
])

eogl = Pipeline([
    ('spectrogram',
     Spectrogram(channel='EOGL', sampling_rate=250, window=500, stride=100)),
    (
    'cutter', CutFrequencies(window=500, sampling_rate=250, lower=0, upper=60)),
    ('psd', PowerSpectralDensityMean(output_dim=51)),
    ('log', LogTransform()),
    ('standard', TwoDScaler())
])

eogr = Pipeline([
    ('spectrogram',
     Spectrogram(channel='EOGR', sampling_rate=250, window=500, stride=100)),
    (
    'cutter', CutFrequencies(window=500, sampling_rate=250, lower=0, upper=60)),
    ('psd', PowerSpectralDensityMean(output_dim=51)),
    ('log', LogTransform()),
    ('standard', TwoDScaler())
])

feats = FeatureUnion(
    [('eeg_spectrogram', eeg_spectrogram), ('emg_psd', emg_psd),
     ('eogl_psd', eogl), ('eogr_psd', eogr)], n_jobs=2)
