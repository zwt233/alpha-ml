import sys
import time
import pickle
import argparse
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.lines as mlines
sns.set_style(style='whitegrid')

plt.rc('text', usetex=True)
plt.rc('font', size=12.0, family='Times New Roman')
plt.rcParams['figure.figsize'] = (8.0, 4.0)
plt.rcParams['text.latex.preamble'] = [r"\usepackage{amsmath}"]
plt.rcParams["legend.frameon"] = True
plt.rcParams["legend.facecolor"] = 'white'
plt.rcParams["legend.edgecolor"] = 'black'
plt.rc('legend', **{'fontsize': 12})

parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=['master', 'daim213'], default='master')
parser.add_argument('--rep', type=int, default=50)
parser.add_argument('--run_count', type=int, default=200)
parser.add_argument('--start_runid', type=int, default=0)
parser.add_argument('--datasets', type=str, default='glass')
args = parser.parse_args()

if args.mode == 'master':
    sys.path.append('/home/thomas/PycharmProjects/alpha-ml')
elif args.mode == 'daim213':
    sys.path.append('/home/liyang/codes/alpha-ml')
else:
    raise ValueError('Invalid mode: %s' % args.mode)

from alphaml.engine.components.data_manager import DataManager
from alphaml.estimators.classifier import Classifier
from alphaml.datasets.cls_dataset.dataset_loader import load_data

from sklearn.model_selection import train_test_split


def get_seeds(dataset, rep_num):
    # Map the dataset to a fixed integer.
    dataset_id = int(''.join([str(ord(c)) for c in dataset[:6] if c.isalpha()])) % 100000
    np.random.seed(dataset_id)
    return np.random.random_integers(10000, size=rep_num)


def test_cash_module():
    rep_num = args.rep
    run_count = args.run_count
    start_id = args.start_runid
    datasets = args.datasets.split(',')
    print(rep_num, run_count, datasets)

    result = dict()
    for dataset in datasets:
        seeds = get_seeds(dataset, rep_num)
        for run_id in range(start_id, rep_num):
            task_format = dataset + '_all_%d'
            X, y, _ = load_data(dataset)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

            seed = seeds[run_id]
            dm = DataManager(X_train, y_train, random_state=seed)
            for optimizer in ['sh_smbo', 'mono_smbo', 'smbo']:
                cls = Classifier(
                    # include_models=['gradient_boosting'],
                    optimizer=optimizer,
                    seed=seed
                ).fit(
                    dm, metric='accuracy', runcount=run_count, task_name=task_format % run_id, update_mode=2)
                acc = cls.score(X_test, y_test)
                key_id = '%s_%d_%s' % (dataset, run_id, optimizer)
                result[key_id] = acc

    # Display and save the test result.
    print(result)
    time_flag = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open('data/runtime_test_result_%s.pkl' % time_flag, 'wb') as f:
        pickle.dump(result, f)


def plot(dataset, rep_num):
    color_list = ['purple', 'royalblue', 'green', 'red', 'brown', 'orange', 'yellowgreen']
    markers = ['s', '^', '2', 'o', 'v', 'p', '*']
    mth_list = ['smac', 'ts_smac']
    lw = 2
    ms = 4
    me = 10

    color_dict, marker_dict = dict(), dict()
    for index, mth in enumerate(mth_list):
        color_dict[mth] = color_list[index]
        marker_dict[mth] = markers[index]

    fig, ax = plt.subplots(1)
    handles = list()
    x_num = 100

    for mth in mth_list:
        perfs = list()
        for id in range(rep_num):
            file_id = 'data/%s_%d_%s.data' % (dataset, id, mth)
            with open(file_id, 'rb') as f:
                data = pickle.load(f)
            perfs.append(data['perfs'])
        perfs = np.mean(perfs, axis=0)
        print(max(perfs), max(perfs[:27]))
        x_num = len(perfs)
        ax.plot(list(range(x_num)), perfs, label=mth, lw=lw, color=color_dict[mth],
                marker=marker_dict[mth], markersize=ms, markevery=me)
        line = mlines.Line2D([], [], color=color_dict[mth], marker=marker_dict[mth],
                             markersize=ms, label=r'\textbf{%s}' % mth.replace("_", "\\_"))
        handles.append(line)

    ax.xaxis.set_major_locator(ticker.MultipleLocator(x_num // 10))
    legend = ax.legend(handles=handles, loc='best')
    ax.set_xlabel('\\textbf{Iteration}', fontsize=15)
    ax.set_ylabel('\\textbf{Validation accuracy}', fontsize=15)
    plt.show()


def debug(dataset, id):
    for mth in ['smac', 'ts_smac']:
        file_id = 'data/%s_%d_%s.data' % (dataset, id, mth)
        with open(file_id, 'rb') as f:
            data = pickle.load(f)

        count_dict = dict()
        perf_dict = dict()
        for config, perf in zip(data['configs'], data['perfs']):
            est = config['estimator']
            if est not in count_dict:
                count_dict[est] = 0
                perf_dict[est] = list()
            count_dict[est] += 1
            perf_dict[est].append(perf)
        print('='*30, mth, '='*30)
        print(count_dict)

        max_id = np.argmax(data['perfs'])
        print(data['configs'][max_id])

        for key in sorted(perf_dict.keys()):
            print(key, np.mean(perf_dict[key]), np.std(perf_dict[key]))
        if mth == 'ts_smac':
            print(data['ts_params'])
            print(data['ts_cnts'])
        print(perf_dict)


if __name__ == "__main__":
    test_cash_module()
    # plot('svmguide4', 1)
