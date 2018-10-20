import numpy as np
import tensorflow as tf
#import tensorflow_probability as tfp
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats, signal
from tensorflow.python.ops import math_ops

loss_a = np.zeros((100,2))
loss_a[:,0] = np.arange(0, 1000,10)
loss_a[:,1] = stats.binom(1000,0.09).pmf(np.arange(100))
plt.subplot(221)
plt.plot(loss_a[:,0], loss_a[:,1],'o-')
plt.title('loss a')
plt.grid('on')

loss_b = np.zeros((100,2))
loss_b[:,0] = np.arange(0, 1000, 10)
loss_b[0,1] = 0.5
loss_b[-1,1] = 0.5
plt.subplot(222)
plt.plot(loss_b[:,0], loss_b[:,1], 'o-')
plt.title('loss b')
plt.grid('on')

values = np.add.outer(loss_a[:,0], loss_b[:,0]).flatten()
probs = np.multiply.outer(loss_a[:,1], loss_b[:,1]).flatten()
df = pd.DataFrame({'values': values, 'probs': probs})
conv = df.groupby('values').sum()
result = conv.reset_index().values
plt.subplot(223)
plt.plot(result[:,0], result[:,1], 'o-')

def combine_losses(loss_a, loss_b):
    client_loss_v = tf.reshape(tf.expand_dims(loss_a[:,0],1) + tf.expand_dims(loss_b[:,0],0), [-1])
    sortation = tf.contrib.framework.argsort(client_loss_v)
    client_loss_p = tf.reshape(tf.einsum('i,j->ij', loss_a[:,1], loss_b[:,1]), [-1])
    cl_v_sorted = tf.gather(client_loss_v, sortation)
    v = tf.concat((tf.fill([100],cl_v_sorted[0]), cl_v_sorted, tf.fill([100],cl_v_sorted[-1])), axis=0)
    cl_p_sorted = tf.gather(client_loss_p, sortation)
    paddings = tf.constant([[100, 100]])
    p = tf.pad(cl_p_sorted, paddings,"CONSTANT")
    cl_v_sum = tf.reduce_mean(tf.reshape(v, (100,102)), axis=1)
    cl_p_sum = tf.reduce_sum(tf.reshape(p, (100,102)), axis=1)
    comb_loss = tf.stack([cl_v_sum, cl_p_sum], 1)
    return comb_loss

comb_loss = combine_losses(tf.Variable(loss_a), tf.Variable(loss_b))
with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    comb_loss = sess.run(comb_loss)
    
plt.subplot(223)
plt.plot(comb_loss[:,0], comb_loss[:,1], 'o-', label="tensorflow")
#plt.plot(values_out2, probs_out2, '.-', label="version 2")
plt.legend()

def deconv(comb_loss,loss_a,loss_b):
    x = tf.cast(comb_loss[:,0], dtype=tf.complex64)
    y = tf.cast(comb_loss[:,1], dtype=tf.complex64)
    yfft = tf.fft(y)
    
    ay = tf.cast(loss_a[:,1], dtype=tf.complex64)
    by = tf.cast(loss_b[:,1], dtype=tf.complex64)
    ayfft = tf.fft(ay)
    byfft = tf.fft(by)
    
    ayfftest = yfft / byfft
    ayest = tf.abs(tf.ifft(ayfftest))
    aest = tf.cast(tf.abs(tf.ifft(ayfft)), dtype=tf.float64)
    best = tf.cast(tf.abs(tf.ifft(byfft)), dtype=tf.float64)
    
    
    return best
    
comb_decov = deconv(comb_loss, loss_a, loss_b)
with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    comb_decov = sess.run(comb_decov)
    
print(comb_decov)
plt.subplot(224)
plt.plot(comb_decov,'o-')
plt.grid('on')

plt.show()
print('Finished')