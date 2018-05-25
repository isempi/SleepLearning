# Code referenced from https://gist.github.com/gyglim/1f8dfb1b5c82627ae3efcfbbadb9f514
import re

import matplotlib
import tensorflow as tf
import numpy as np
import scipy.misc
from textwrap import wrap
import itertools
import tfplot
from sklearn.metrics import confusion_matrix

try:
    from StringIO import StringIO  # Python 2.7
except ImportError:
    from io import BytesIO  # Python 3.x


class Logger(object):

    def __init__(self, log_dir):
        """Create a summary writer logging to log_dir."""
        self.writer = tf.summary.FileWriter(log_dir)

    def scalar_summary(self, tag, value, step):
        """Log a scalar variable."""
        summary = tf.Summary(
            value=[tf.Summary.Value(tag=tag, simple_value=value)])
        self.writer.add_summary(summary, step)

    def cm_summary(self, correct_labels, predict_labels, step, normalize=True):
        """
        Parameters:
            correct_labels                  : These are your true classification categories.
            predict_labels                  : These are you predicted classification categories
            step                            : Training step (batch/epoch)
        """
        # TODO: fix for only 3 labels

        cm = confusion_matrix(correct_labels, predict_labels)
        number_format = 'd'
        if normalize:
            cm = cm.astype('float') * 1 / cm.sum(axis=1)[:, np.newaxis]
            cm = np.nan_to_num(cm, copy=True)
            number_format = '.2f'
            #cm = cm.astype('int')

        np.set_printoptions(precision=2)
        ###fig, ax = matplotlib.figure.Figure()

        fig = matplotlib.figure.Figure(figsize=(3, 3), dpi=320, facecolor='w',
                                       edgecolor='k')
        ax = fig.add_subplot(1, 1, 1)
        im = ax.imshow(cm, cmap='Oranges')
        classes = ['W', 'N1', 'N2', 'N3', 'REM']

        tick_marks = np.arange(len(classes))

        ax.set_xlabel('Predicted', fontsize=10, weight='bold')
        ax.set_xticks(tick_marks)
        c = ax.set_xticklabels(classes, fontsize=8, rotation=-90, ha='center')
        ax.xaxis.set_label_position('bottom')
        ax.xaxis.tick_bottom()

        ax.set_ylabel('True Label', fontsize=10, weight='bold')
        ax.set_yticks(tick_marks)
        ax.set_yticklabels(classes, fontsize=8, va='center')
        ax.yaxis.set_label_position('left')
        ax.yaxis.tick_left()

        for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
            ax.text(j, i, format(cm[i, j], number_format) if cm[i, j] != 0 else '.',
                    horizontalalignment="center", fontsize=8,
                    verticalalignment='center', color="black")
        fig.set_tight_layout(True)
        summary = tfplot.figure.to_summary(fig, tag='cm')
        self.writer.add_summary(summary, step)

    def image_summary(self, tag, images, step):
        """Log a list of images."""

        img_summaries = []
        for i, img in enumerate(images):
            # Write the image to a string
            try:
                s = StringIO()
            except:
                s = BytesIO()
            scipy.misc.toimage(img).save(s, format="png")

            # Create an Image object
            img_sum = tf.Summary.Image(encoded_image_string=s.getvalue(),
                                       height=img.shape[0],
                                       width=img.shape[1])
            # Create a Summary value
            img_summaries.append(
                tf.Summary.Value(tag='%s/%d' % (tag, i), image=img_sum))

        # Create and write Summary
        summary = tf.Summary(value=img_summaries)
        self.writer.add_summary(summary, step)

    def histo_summary(self, tag, values, step, bins=1000):
        """Log a histogram of the tensor of values."""

        # Create a histogram using numpy
        counts, bin_edges = np.histogram(values, bins=bins)

        # Fill the fields of the histogram proto
        hist = tf.HistogramProto()
        hist.min = float(np.min(values))
        hist.max = float(np.max(values))
        hist.num = int(np.prod(values.shape))
        hist.sum = float(np.sum(values))
        hist.sum_squares = float(np.sum(values ** 2))

        # Drop the start of the first bin
        bin_edges = bin_edges[1:]

        # Add bin edges and counts
        for edge in bin_edges:
            hist.bucket_limit.append(edge)
        for c in counts:
            hist.bucket.append(c)

        # Create and write Summary
        summary = tf.Summary(value=[tf.Summary.Value(tag=tag, histo=hist)])
        self.writer.add_summary(summary, step)
        self.writer.flush()