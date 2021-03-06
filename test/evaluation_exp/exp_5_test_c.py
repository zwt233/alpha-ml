import os
import sys
import pickle
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=['master', 'daim213', 'gc'], default='master')
parser.add_argument('--start_runid', type=int, default=0)
parser.add_argument('--datasets', type=str, default='pc4')
args = parser.parse_args()

if args.mode == 'master':
    project_folder = '/home/thomas/PycharmProjects/alpha-ml'
elif args.mode == 'daim213':
    project_folder = '/home/liyang/codes/alpha-ml'
elif args.mode == 'gc':
    project_folder = '/home/contact_ds3lab/testinstall/alpha-ml'
else:
    raise ValueError('Invalid mode: %s' % args.mode)
sys.path.append(project_folder)

from alphaml.engine.components.data_manager import DataManager
from alphaml.estimators.classifier import Classifier
from alphaml.datasets.cls_dataset.dataset_loader import load_data
from alphaml.utils.rand import get_seeds
from sklearn.model_selection import train_test_split


def evaluate_c():
    rep_num = 10
    run_count = 500
    start_id = args.start_runid
    datasets = args.datasets.split(',')
    task_id = 'exp5_eval_c'
    print(rep_num, run_count, datasets, task_id)

    for dataset in datasets:
        # Make directories.
        dataset_id = dataset.split('_')[0]
        save_dir = "data/%s/" % dataset_id
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        result = dict()
        seeds = get_seeds(dataset, start_id+rep_num)
        for run_id in range(start_id, start_id + rep_num):
            seed = seeds[run_id]

            # Dataset partition.
            X, y, _ = load_data(dataset)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
            dm = DataManager(X_train, y_train)

            # Test each optimizer algorithm:
            for p in [1, 4, 10, 14, 16, 20]:
                task_name = dataset + '_%s_%d_%d_%d' % (task_id, run_count, run_id, p)
                mode = 3
                optimizer = 'mono_smbo'

                print('Test %s optimizer => %s' % (optimizer, task_name))

                # Construct the AutoML classifier.
                cls = Classifier(optimizer=optimizer, seed=seed).fit(
                    dm, metric='accuracy', runcount=run_count,
                    task_name=task_name, update_mode=mode, param=p)
                acc = cls.score(X_test, y_test)
                key_id = '%s_%d_%d_%d_%s' % (dataset, run_count, run_id, p, optimizer)
                result[key_id] = acc

            # Display and save the test result.
            print(result)
            with open('data/%s/%s_test_%s_%d_%d_%d.pkl' % (dataset_id, dataset,
                                                               task_id, run_count, rep_num, start_id), 'wb') as f:
                pickle.dump(result, f)


if __name__ == "__main__":
    evaluate_c()
