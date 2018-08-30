import math, time, random
import numpy as np
import tensorflow as tf

from log_utils import *

def rewards_to_qvals(t_r_l, gamma):
  T = t_r_l.shape[0]
  # reward = average of all following rewards
  # for t in range(T):
  #   t_r_l[t, 0] = np.mean(t_r_l[t:, 0])
  
  # for t in range(T):
  #   cumw, cumr = 0, 0
  #   for i, r in enumerate(t_r_l[t:, 0] ):
  #     cumw += gamma**i
  #     cumr += gamma**i * r
  #   t_r_l[t, 0] = cumr/cumw
  # return t_r_l
  
  t_dr_l = np.zeros((T, 1))
  cumw, cumr = 0, 0
  for t in range(T-1, -1, -1):
    cumr = t_r_l[t, 0] + gamma*cumr
    # cumw = 1 + gamma*cumw
    # t_dr_l[t, 0] = cumr/cumw
    t_dr_l[t, 0] = cumr
  return t_dr_l

# #######################################  Value Estimator  ###################################### #
class VEster(object): # Value Estimator
  def __init__(self, s_len, nn_len):
    self.s_len = s_len
    self.nn_len = nn_len
    
    self.init()
  
  def __repr__(self):
    return "VEster[s_len= {}]".format(self.s_len)
  
  def init(self):
    # N x T x s_len
    self.s_ph = tf.placeholder(shape=(None, None, self.s_len), dtype=tf.float32)
    # self.hidden1 = tf.contrib.layers.fully_connected(self.s_ph, self.nn_len, activation_fn=tf.nn.relu)
    # self.hidden2 = tf.contrib.layers.fully_connected(self.hidden1, self.nn_len, activation_fn=tf.nn.relu)
    # self.v = tf.contrib.layers.fully_connected(self.hidden2, 1, activation_fn=None)
    self.hidden = tf.contrib.layers.fully_connected(self.s_ph, self.nn_len, activation_fn=tf.nn.relu)
    self.v = tf.contrib.layers.fully_connected(self.hidden, 1, activation_fn=None)
    
    self.sampled_v = tf.placeholder(shape=(None, None, 1), dtype=tf.float32)
    # self.loss = tf.reduce_sum(tf.squared_difference(self.v, self.sampled_v) )
    self.loss = tf.losses.mean_squared_error(self.v, self.sampled_v)
    
    # self.optimizer = tf.train.GradientDescentOptimizer(0.01)
    self.optimizer = tf.train.AdamOptimizer(0.01)
    self.train_op = self.optimizer.minimize(self.loss)
    
    self.sess = tf.Session()
    self.sess.run(tf.global_variables_initializer() )
  
  def train_w_mult_trajs(self, n_t_s_l, n_t_v_l):
    _, loss = self.sess.run([self.train_op, self.loss],
                            feed_dict={self.s_ph: n_t_s_l,
                                       self.sampled_v: n_t_v_l} )
    print("VEster:: loss= {}".format(loss) )
  
  def get_v(self, n_t_s_l):
    return self.sess.run(self.v,
                         feed_dict={self.s_ph: n_t_s_l} )

# ####################################  Policy Gradient Learner  ################################# #
class PolicyGradLearner(object):
  def __init__(self, s_len, a_len, nn_len=10, w_actorcritic=False, save_dir='save'):
    self.s_len = s_len
    self.a_len = a_len
    self.nn_len = nn_len
    self.w_actorcritic = w_actorcritic
    
    self.v_ester = VEster(s_len, nn_len)
    self.gamma = 0.99 # 0.8
    self.init()
    
    self.save_name = '{}/PolicyGradLearner_gamma{}_slen{}_alen{}_nnlen{}_wactorcritic{}'.format(save_dir, self.gamma, s_len, a_len, nn_len, w_actorcritic)
    self.saver = tf.train.Saver(max_to_keep=5)
  
  def __repr__(self):
    return "PolicyGradLearner[s_len= {}, a_len= {}, nn_len= {}, gamma= {}, w_actorcritic= {}]".format(self.s_len, self.a_len, self.nn_len, self.gamma, self.w_actorcritic)
  
  def save(self, step):
    save_path = self.saver.save(self.sess, self.save_name, global_step=step)
    log(WARNING, "saved; ", save_path=save_path)
  
  def restore(self, step):
    try:
      save_path = '{}-{}'.format(self.save_name, step)
      self.saver.restore(self.sess, save_path)
      log(WARNING, "restored; ", save_path=save_path)
      return True
    except:
      return False
  
  def init(self):
    # N x T x s_len
    self.s_ph = tf.placeholder(tf.float32, shape=(None, None, self.s_len) )
    hidden1 = tf.contrib.layers.fully_connected(self.s_ph, self.nn_len, activation_fn=tf.nn.relu)
    hidden2 = tf.contrib.layers.fully_connected(hidden1, self.nn_len, activation_fn=tf.nn.relu)
    self.a_probs = tf.contrib.layers.fully_connected(hidden2, self.a_len, activation_fn=tf.nn.softmax)
    # self.s_ph = tf.placeholder(tf.float32, shape=(None, None, self.s_len) )
    # hidden1 = tf.contrib.layers.fully_connected(self.s_ph, self.nn_len, activation_fn=tf.nn.relu)
    # self.a_probs = tf.contrib.layers.fully_connected(hidden1, self.a_len, activation_fn=tf.nn.softmax)
    
    self.a_ph = tf.placeholder(tf.int32, shape=(None, None, 1), name='a_ph')
    self.q_ph = tf.placeholder(tf.float32, shape=(None, None, 1), name='q_ph')
    self.v_ph = tf.placeholder(tf.float32, shape=(None, None, 1), name='v_ph')
    
    sh = tf.shape(self.a_probs)
    N, T = sh[0], sh[1]
    indices = tf.range(0, N*T)*sh[2] + tf.reshape(self.a_ph, [-1] )
    self.resp_outputs = tf.reshape(tf.gather(tf.reshape(self.a_probs, [-1] ), indices), (N, T, 1) )
    self.loss = -tf.reduce_mean(tf.reduce_sum(tf.log(self.resp_outputs)*(self.q_ph - self.v_ph), axis=1), axis=0)
    
    self.optimizer = tf.train.AdamOptimizer(0.01) # tf.train.GradientDescentOptimizer(0.01)
    self.train_op = self.optimizer.minimize(self.loss)
    
    self.sess = tf.Session()
    self.sess.run(tf.global_variables_initializer() )
  
  def train_w_mult_trajs(self, n_t_s_l, n_t_a_l, n_t_r_l):
    # All trajectories use the same policy
    N = len(n_t_s_l)
    T = len(n_t_s_l[0] )
    # print("n_t_s_l.shape= {}".format(n_t_s_l.shape) )
    # print("avg r= {}".format(np.mean(n_t_r_l) ) )
    
    if not self.w_actorcritic:
      n_t_q_l = np.zeros((N, T, 1))
      for n in range(N):
        n_t_q_l[n] = rewards_to_qvals(n_t_r_l[n], self.gamma)
      # print("n_t_q_l= {}".format(n_t_q_l) )
      # print("n_t_q_l.shape= {}".format(n_t_q_l.shape) )
      print("PolicyGradLearner:: avg q= {}".format(np.mean(n_t_q_l) ) )
      
      t_avgq_l = np.array([np.mean(n_t_q_l[:, t, 0] ) for t in range(T) ] ).reshape((T, 1))
      # m = np.mean(n_t_q_l)
      # t_avgq_l = np.array([m for t in range(T) ] ).reshape((T, 1))
      n_t_v_l = np.zeros((N, T, 1))
      for n in range(N):
        n_t_v_l[n] = t_avgq_l
      # print("n_t_v_l= {}".format(n_t_v_l) )
      # print("n_t_v_l.shape= {}".format(n_t_v_l.shape) )
      
      loss, _ = self.sess.run([self.loss, self.train_op],
                              feed_dict={self.s_ph: n_t_s_l,
                                         self.a_ph: n_t_a_l,
                                         self.q_ph: n_t_q_l,
                                         self.v_ph: n_t_v_l} )
    else:
      # Policy gradient by getting baseline values from actor-critic
      n_t_v_l = np.zeros((N, T, 1))
      n_t_vest_l = self.v_ester.get_v(n_t_s_l)
      for t in range(T-1):
        n_t_v_l[:, t] = n_t_r_l[:, t] + self.gamma*n_t_vest_l[:, t+1]
      n_t_v_l[:, T-1] = n_t_r_l[:, T-1]
      self.v_ester.train_w_mult_trajs(n_t_s_l, n_t_v_l)
      
      n_t_v_l = self.v_ester.get_v(n_t_s_l)
      n_t_q_l = np.zeros((N, T, 1))
      # for n in range(N):
      #   for t in range(T-1):
      #     n_t_q_l[n, t] = n_t_r_l[n, t] + self.gamma*n_t_v_l[n, t+1]
      #   n_t_q_l[n, T-1] = n_t_r_l[n, t]
      for t in range(T-1):
        n_t_q_l[:, t] = n_t_r_l[:, t] + self.gamma*n_t_v_l[:, t+1]
      n_t_q_l[:, T-1] = n_t_r_l[:, T-1]
      loss, _ = self.sess.run([self.loss, self.train_op],
                              feed_dict={self.s_ph: n_t_s_l,
                                         self.a_ph: n_t_a_l,
                                         self.q_ph: n_t_q_l,
                                         self.v_ph: n_t_v_l} )
    log(INFO, "PolicyGradLearner;", loss=loss)
  
  def get_action_val(self, s):
    a = self.sess.run(self.a_probs, feed_dict={self.s_ph: [[s]] } )
    return a[0][0]
  
  def get_action_dist(self, s):
    a_probs = self.sess.run(self.a_probs, feed_dict={self.s_ph: [[s]] } )
    return np.array(a_probs[0][0] )
  
  def get_random_action(self, s):
    a_probs = self.sess.run(self.a_probs, feed_dict={self.s_ph: [[s]] } )
    a_dist = np.array(a_probs[0][0] )
    # log(WARNING, "", s=s, a_dist=a_dist)
    a = np.random.choice(a_dist, 1, p=a_dist)
    a = np.argmax(a_dist == a)
    return a
  
  def get_max_action(self, s):
    a_probs = self.sess.run(self.a_probs, feed_dict={self.s_ph: [[s]] } )
    a_dist = a_probs[0][0]
    # print("a_dist= {}".format(a_dist) )
    return np.argmax(a_dist)  

# ###########################################  Q Learning  ####################################### #
class QLearner(object):
  def __init__(self, s_len, a_len, nn_len=10):
    self.s_len = s_len
    self.a_len = a_len
    self.nn_len = nn_len
    
    self.gamma = 0.99
    self.eps = 0.1
    self.init()
    
  def __repr__(self):
    return "QLearner[s_len= {}, a_len= {}]".format(self.s_len, self.a_len)
  
  def init(self):
    # N x T x s_len
    self.s_ph = tf.placeholder(tf.float32, shape=(None, None, self.s_len) )
    hidden1 = tf.contrib.layers.fully_connected(self.s_ph, self.nn_len, activation_fn=tf.nn.relu)
    hidden2 = tf.contrib.layers.fully_connected(hidden1, self.nn_len, activation_fn=tf.nn.relu)
    self.Qa_ph = tf.contrib.layers.fully_connected(hidden2, self.a_len, activation_fn=None)
    
    self.a_ph = tf.placeholder(tf.int32, shape=(None, None, 1), name="a_ph")
    self.targetq_ph = tf.placeholder(tf.float32, shape=(None, None, 1), name="q_ph")
    
    sh = tf.shape(self.Qa_ph)
    N, T = sh[0], sh[1]
    indices = tf.range(0, N*T)*sh[2] + tf.reshape(self.a_ph, [-1] )
    self.resp_outputs = tf.reshape(tf.gather(tf.reshape(self.Qa_ph, [-1] ), indices), (sh[0], sh[1], 1) )
    self.loss = tf.losses.mean_squared_error(self.resp_outputs, self.targetq_ph)
    
    self.optimizer = tf.train.AdamOptimizer(0.01)
    self.train_op = self.optimizer.minimize(self.loss)
    
    self.sess = tf.Session()
    self.sess.run(tf.global_variables_initializer() )
  
  def train_w_mult_trajs(self, n_t_s_l, n_t_a_l, n_t_r_l):
    N = len(n_t_s_l)
    T = len(n_t_s_l[0] )
    
    # n_t_q_l = self.sess.run(self.Qa_ph,
    #                         feed_dict={self.s_ph: n_t_s_l} )
    # n_t_targetq_l = np.zeros((N, T, 1))
    # for n in range(N):
    #   for t in range(T):
    #     if t < T-1:
    #       n_t_targetq_l[n, t, 0] = n_t_r_l[n, t, 0] + self.gamma*max(n_t_q_l[n, t+1, :] )
    #     else:
    #       n_t_targetq_l[n, t, 0] = n_t_r_l[n, t, 0]
    
    n_t_targetq_l = np.zeros((N, T, 1))
    for n in range(N):
      n_t_targetq_l[n] = rewards_to_qvals(n_t_r_l[n], self.gamma)
    
    loss, _ = self.sess.run([self.loss, self.train_op],
                            feed_dict={self.s_ph: n_t_s_l,
                                       self.a_ph: n_t_a_l,
                                       self.targetq_ph: n_t_targetq_l} )
    print("QLearner:: loss= {}".format(loss) )
    # self.eps *= 0.95
  
  def get_random_action(self, s):
    if random.uniform(0, 1) < self.eps:
      return np.random.randint(self.a_len, size=1)[0]
    else:
      qa_l = self.sess.run(self.Qa_ph,
                           feed_dict={self.s_ph: [[s]] } )
      return np.argmax(qa_l)
  
  def get_max_action(self, s):
    qa_l = self.sess.run(self.Qa_ph,
                         feed_dict={self.s_ph: [[s]] } )
    return np.argmax(qa_l)

# #############################################  Test  ########################################### #
def test():
  s_len, a_len, nn_len = 3, 3, 10
  scher = PolicyGradLearner(s_len, a_len, nn_len)
  # scher = QLearner(s_len, a_len, nn_len)
  
  def state():
    s = np.random.randint(10, size=s_len)
    sum_s = sum(s)
    return s/sum_s if sum_s != 0 else s
  
  def reward(s, a):
    # s_min = min(s)
    # r = 10 if s[a] == s_min else 0
    # return min(100, 1/(0.001 + s[a] - min(s) ) )
    # return 100*math.exp(-(s[a] - min(s) ) )
    return 1/(0.1 + s[a] - min(s) )
  
  def evaluate():
    num_shortest_found = 0
    for e in range(100):
      s = state()
      a = scher.get_max_action(s)
      if s[a] - min(s) < 0.01:
        num_shortest_found += 1
    print("freq shortest found= {}".format(num_shortest_found/100) )
  
  def train_w_mult_trajs():
    N, T = 10, 100
    def gen_N_traj():
      n_t_s_l, n_t_a_l, n_t_r_l = np.zeros((N, T, s_len)), np.zeros((N, T, 1)), np.zeros((N, T, 1))
      for n in range(N):
        for t in range(T):
          s = state()
          a = scher.get_random_action(s)
          n_t_s_l[n, t, :] = s
          n_t_a_l[n, t, :] = a
          n_t_r_l[n, t, :] = reward(s, a)
      return n_t_s_l, n_t_a_l, n_t_r_l
    
    for i in range(100*20):
      n_t_s_l, n_t_a_l, n_t_r_l = gen_N_traj()
      scher.train_w_mult_trajs(n_t_s_l, n_t_a_l, n_t_r_l)
      if i % 10 == 0:
        evaluate()
  train_w_mult_trajs()

def vsimple_regress():
  s_len = 3
  T = 100
  def state():
    s = np.random.randint(10, size=s_len)
    sum_s = sum(s)
    return s/sum_s if sum_s != 0 else s
  
  def reward(s):
    return 10*max(s)
  
  def sample_traj():
    t_s_l, t_r_l = np.zeros((T, s_len)), np.zeros((T, 1))
    for t in range(T):
      s = state()
      t_s_l[t, :] = s
      t_r_l[t, :] = reward(s)
    return t_s_l, t_r_l
  
  value_ester = VEster(s_len, nn_len=10, straj_training=False)
  for i in range(100*40):
    t_s_l, t_r_l = sample_traj()
    value_ester.train_w_single_traj(t_s_l, t_r_l)

if __name__ == "__main__":
  test()
  # vsimple_regress()
  