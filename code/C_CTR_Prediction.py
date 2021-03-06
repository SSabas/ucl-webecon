"""
Project:
    COMPGW02/M041 Web Economics Coursework Project

Description:
    In this assignment, we are required to work on an online advertising problem. We will help advertisers to form
    a bidding strategy in order to place their ads online in a realtime bidding system. We are required to train a
    bidding strategy based on a provided advertising impression training set. This project aims to help us understand
    some basic concepts and write a computer program in real-time bidding based display advertising. As we will be
    evaluated both as a group as well as individually, part of the assignment is to train a model of our choice
    independently. The performance of the model trained by the team, which is either a combination of the
    individually developed models or the best performing individually-developed model, will be (mainly) evaluated
    on the Click-through Rate achieved on a provided test set.

Authors:
  Sven Sabas

Date:
  22/02/2018
"""

# ------------------------------ IMPORT LIBRARIES --------------------------------- #

import pandas as pd
import xgboost
from pylab import rcParams
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import roc_auc_score
from sklearn.metrics import make_scorer
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import roc_curve
from sklearn.metrics import auc
import matplotlib.pyplot as plt
from sklearn.ensemble import ExtraTreesClassifier
from mlxtend.classifier import StackingCVClassifier
from sklearn.ensemble import RandomForestClassifier
from fastFM import als
import scipy.sparse as sp
from sklearn.externals import joblib
from sklearn import svm
from sknn.mlp import Classifier, Layer
import os

# --------------------------------- FITTING --------------------------------------- #


# --- PLOT ROC CURVE
def plot_ROC_curve(data, prediction, model=None, minority_class=None):
    """
    Function to plot the ROC curve with AUC.
    """

    # Compute fpr, tpr, thresholds and roc auc
    fpr, tpr, thresholds = roc_curve(data, prediction)
    roc_auc = roc_auc_score(data, prediction)

    if model != None:
        label_title = '%s (AUC = %0.3f)' % (model, roc_auc)

    else:
        label_title = 'ROC Curve (AUC = %0.3f)' % roc_auc

    if minority_class != None:
        plot_title = 'ROC Curve (Sample with %.1f%% Minority Class)' %(minority_class*100)

    else:
        plot_title = 'ROC'

    # Plot ROC curve
   # plt.figure(figsize=(3.3 * 1.2, 2.2 * 1.2))
    rcParams['figure.figsize'] = 3.3 * 1.2, 2.2 * 1.4
    plt.tick_params(labelsize=6)
    plt.plot(fpr, tpr, label=label_title)
    plt.plot([0, 1], [0, 1], 'k--')  # random predictions curve
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.0])
    plt.xlabel('False Positive Rate or (1 - Specifity)', fontsize=8)
    plt.ylabel('True Positive Rate or (Sensitivity)', fontsize=8)
    plt.title(plot_title, fontsize=10)
    plt.legend(loc="lower right", fontsize=6)


# --- LOGISTIC REGRESSION
def logistic_model(train, validation,
                   parameters = {'C': [0.1, 1, 2, 5, 10],
                  'penalty': ['l1', 'l2'],
                  'class_weight': ['unbalanced'],
                  'solver': ['saga'],
                  'tol': [0.01],
                  'max_iter': [1]},
                   use_gridsearch = 'yes',
                   refit = 'yes',
                   refit_iter = 100,
                   use_saved_model = 'no',
                   to_plot ='yes',
                   random_seed = 500,
                   save_model = 'yes'):

    if use_gridsearch == 'yes':

        print('Running gridsearch for hyperparameter tuning.')

        # Create model object
        model = GridSearchCV(LogisticRegression(), parameters, cv=3, verbose=10, scoring = 'roc_auc')

        # Fit the model
        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1), train['click'])

        # View best hyperparameters
        print('Best Penalty:', model.best_estimator_.get_params()['penalty'])
        print('Best C:', model.best_estimator_.get_params()['C'])

        if refit == 'yes':

            # If refit, run
            model = LogisticRegression(C=model.best_estimator_.get_params()['C'],
                                       penalty=model.best_estimator_.get_params()['penalty'],
                                       solver=model.best_estimator_.get_params()['solver'],
                                       class_weight=model.best_estimator_.get_params()['class_weight'],
                                       max_iter=refit_iter,
                                       n_jobs=model.best_estimator_.get_params()['n_jobs'],
                                       tol=model.best_estimator_.get_params()['tol'],
                                       random_state=random_seed,
                                       verbose=10)

            # Refit
            model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1), train['click'])

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

        else:
            prediction = model.best_estimator_.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

    elif use_saved_model == 'yes':

        # Load from saved files
        model_filename = os.getcwd() + "/models/logistic_model.pkl"
        saved_model = joblib.load(model_filename)

        # View best hyperparameters
        print('Saved Model Penalty:', saved_model.get_params()['penalty'])
        print('Saved Model C:', saved_model.get_params()['C'])

        if refit == 'yes':

            # If refit, run
            model = LogisticRegression(C=saved_model.get_params()['C'],
                                       penalty=saved_model.get_params()['penalty'],
                                       solver=saved_model.get_params()['solver'],
                                       class_weight=saved_model.get_params()['class_weight'],
                                       max_iter=refit_iter,
                                       n_jobs=saved_model.get_params()['n_jobs'],
                                       tol=saved_model.get_params()['tol'],
                                       random_state=random_seed,
                                       verbose=10)

            # Fit the model
            model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1), train['click'])

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

        else:
            prediction = saved_model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))
            model = saved_model
    else:

        # Fit the model
        model = LogisticRegression(C=parameters['C'], penalty=parameters['penalty'], solver='saga',
                                   class_weight = parameters['class_weight'],
                                   max_iter = parameters['max_iter'],
                                   n_jobs = parameters['n_jobs'],
                                   tol=parameters['tol'],
                                   random_state = random_seed,
                                   verbose=10)

        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1), train['click'])
        prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

    # Print scores
    print("AUC: %0.5f for Logistic Model"% (roc_auc_score(validation['click'], prediction[:, 1])))

    # Whether to save the model
    if save_model == 'yes':

        print('Saving the logistic model to the disc.')
        model_filename = os.getcwd() + "/models/logistic_model.pkl"
        joblib.dump(model, model_filename, compress=9)

    if to_plot == 'yes':

        plot_ROC_curve(validation['click'], prediction[:, 1])

    return model, prediction[:,1]


# --- RANDOM FOREST
def random_forest(train, validation,
                   parameters = {'max_depth': [2,3,4,5,6,7,8,9,10,11,12, None],
              'min_samples_split' :[4,5,6],
              "n_estimators" : [10],
              "min_samples_leaf": [1,2,3,4,5],
              "max_features": [4,5,6,"sqrt"],
              "criterion": ['gini','entropy'],
                                 'random_state': 500},
                   use_gridsearch = 'yes',
                   refit = 'yes',
                   refit_iter = 100,
                   use_saved_model = 'no',
                  save_model = 'no',
                   to_plot ='yes',
                   random_seed = 500):

    if use_gridsearch == 'yes':

        # Create model object
        model = GridSearchCV(RandomForestClassifier(), parameters, cv=3, verbose=10, scoring = 'roc_auc')

        # Fit the model
        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1), train['click'])

        # View best hyperparameters
        print('Best Max Depth:', model.best_estimator_.get_params()['max_depth'])
        print('Best Min Sample Split:', model.best_estimator_.get_params()['min_samples_split'])
        print('Best Min Samples Leaf:', model.best_estimator_.get_params()['min_samples_leaf'])
        print('Best Max Features:', model.best_estimator_.get_params()['max_features'])
        print('Best Criterion:', model.best_estimator_.get_params()['criterion'])

        if refit == 'yes':

            # If refit, run
            model = RandomForestClassifier(max_depth=model.best_estimator_.get_params()["max_depth"]
                                   , max_features=model.best_estimator_.get_params()['max_features']
                                   , min_samples_leaf=model.best_estimator_.get_params()['min_samples_leaf']
                                   , min_samples_split=model.best_estimator_.get_params()['min_samples_split']
                                   , criterion=model.best_estimator_.get_params()['criterion']
                                   , n_estimators=refit_iter
                                   , n_jobs=3
                                   , verbose=10
                                           , random_state= random_seed)

            # Refit
            model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1), train['click'])

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

        else:
            prediction = model.best_estimator_.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

    elif use_saved_model == 'yes':

        # Load from saved files
        model_filename = os.getcwd() + "/models/rf_model.pkl"
        saved_model = joblib.load(model_filename)

        # View saved model hyperparameters
        print('Saved Model Max Depth:', saved_model.get_params()['max_depth'])
        print('Saved Model Min Sample Split:', saved_model.get_params()['min_samples_split'])
        print('Saved Model Min Samples Leaf:', saved_model.get_params()['min_samples_leaf'])
        print('Saved Model Max Features:', saved_model.get_params()['max_features'])
        print('Saved Model Criterion:', saved_model.get_params()['criterion'])

        if refit == 'yes':

            # If refit, run
            model = RandomForestClassifier(max_depth=saved_model.get_params()["max_depth"]
                                   , max_features=saved_model.get_params()['max_features']
                                   , min_samples_leaf=saved_model.get_params()['min_samples_leaf']
                                   , min_samples_split=saved_model.get_params()['min_samples_split']
                                   , criterion=saved_model.get_params()['criterion']
                                   , n_estimators=refit_iter
                                   , n_jobs=3
                                   , verbose=10
                                           , random_state=random_seed)
            # Fit the model
            model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1), train['click'])

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

        else:
            prediction = saved_model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))
            model = saved_model

    else:

        # Fit the model
        model = RandomForestClassifier(max_depth=parameters["max_depth"]
                                       , max_features=parameters['max_features']
                                       , min_samples_leaf=parameters['min_samples_leaf']
                                       , min_samples_split=parameters['min_samples_split']
                                       , criterion=parameters['criterion']
                                       , n_estimators=parameters['n_estimators']
                                       , n_jobs=3
                                       , verbose=10
                                       , random_state=random_seed)

        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1), train['click'])
        prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

    # Print scores
    print("AUC: %0.5f for Random Forest Model"% (roc_auc_score(validation['click'], prediction[:, 1])))

    # Whether to save the model
    if save_model == 'yes':

        print('Saving the random forest model to the disc.')
        model_filename = os.getcwd() + "/models/rf_model.pkl"
        joblib.dump(model, model_filename, compress=9)

    if to_plot == 'yes':

        plot_ROC_curve(validation['click'], prediction[:, 1])

    return model, prediction[:,1]


# --- EXTREME RANDOM FOREST
def extreme_random_forest(train, validation,
                   parameters = {'max_depth': [2,3,4,5,6,7,8,9,10,11,12, None],
              'min_samples_split' :[4,5,6],
              "n_estimators" : [10],
              "min_samples_leaf": [1,2,3,4,5],
              "max_features": [4,5,6,"sqrt"],
              "criterion": ['gini','entropy']},
                   use_gridsearch = 'yes',
                   refit = 'yes',
                   refit_iter = 100,
                   use_saved_model = 'no',
                          save_model = 'yes',
                   to_plot ='yes',
                   random_seed = 500):


    if use_gridsearch == 'yes':

        # Create model object
        model = GridSearchCV(ExtraTreesClassifier(), parameters, cv=3, verbose=10, scoring = 'roc_auc')

        # Fit the model
        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1), train['click'])

        # View best hyperparameters
        print('Best Max Depth:', model.best_estimator_.get_params()['max_depth'])
        print('Best Min Sample Split:', model.best_estimator_.get_params()['min_samples_split'])
        print('Best Min Samples Leaf:', model.best_estimator_.get_params()['min_samples_leaf'])
        print('Best Max Features:', model.best_estimator_.get_params()['max_features'])
        print('Best Criterion:', model.best_estimator_.get_params()['criterion'])

        if refit == 'yes':

            # If refit, run
            model = ExtraTreesClassifier(max_depth=model.best_estimator_.get_params()["max_depth"]
                                   , max_features=model.best_estimator_.get_params()['max_features']
                                   , min_samples_leaf=model.best_estimator_.get_params()['min_samples_leaf']
                                   , min_samples_split=model.best_estimator_.get_params()['min_samples_split']
                                   , criterion=model.best_estimator_.get_params()['criterion']
                                   , n_estimators=refit_iter
                                   , n_jobs=3
                                   , verbose=10
                                         , random_state = random_seed)

            # Refit
            model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1), train['click'])

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

        else:
            prediction = model.best_estimator_.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

    elif use_saved_model == 'yes':

        # Load from saved files
        model_filename = os.getcwd() + "/models/erf_model.pkl"
        saved_model = joblib.load(model_filename)

        # View saved model hyperparameters
        print('Saved Model Max Depth:', saved_model.get_params()['max_depth'])
        print('Saved Model Min Sample Split:', saved_model.get_params()['min_samples_split'])
        print('Saved Model Min Samples Leaf:', saved_model.get_params()['min_samples_leaf'])
        print('Saved Model Max Features:', saved_model.get_params()['max_features'])
        print('Saved Model Criterion:', saved_model.get_params()['criterion'])

        if refit == 'yes':

            # If refit, run
            model = ExtraTreesClassifier(max_depth=saved_model.get_params()["max_depth"]
                                   , max_features=saved_model.get_params()['max_features']
                                   , min_samples_leaf=saved_model.get_params()['min_samples_leaf']
                                   , min_samples_split=saved_model.get_params()['min_samples_split']
                                   , criterion=saved_model.get_params()['criterion']
                                   , n_estimators=refit_iter
                                   , n_jobs=3
                                   , verbose=10
                                         , random_state=random_seed)
            # Fit the model
            model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1), train['click'])

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

        else:
            prediction = saved_model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))
            model = saved_model

    else:

        # Fit the model
        model = ExtraTreesClassifier(max_depth=parameters["max_depth"]
                                       , max_features=parameters['max_features']
                                       , min_samples_leaf=parameters['min_samples_leaf']
                                       , min_samples_split=parameters['min_samples_split']
                                       , criterion=parameters['criterion']
                                       , n_estimators=parameters['n_estimators']
                                       , n_jobs=3
                                       , verbose=10
                                     , random_state=random_seed)

        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1), train['click'])
        prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

    # Whether to save the model
    if save_model == 'yes':

        print('Saving the extreme random forest model to the disc.')
        model_filename = os.getcwd() + "/models/erf_model.pkl"
        joblib.dump(model, model_filename, compress=9)

    # Print scores
    print("AUC: %0.5f for Extreme Random Forest Model"% (roc_auc_score(validation['click'], prediction[:, 1])))

    if to_plot == 'yes':

        plot_ROC_curve(validation['click'], prediction[:, 1])

    return model, prediction[:,1]


# --- GRADIENT BOOSTED TREES (XGBOOST)
def gradient_boosted_trees(train, validation,
                           parameters={'max_depth': [15, 20],
                                       "n_estimators": [10],
                                       "learning_rate": [0.05, 0.1],
                                       "colsample_bytrees": [0.5],
                                       "reg_alpha": [0.1],
                                       "reg_lambda": [0.1],
                                       "subsample": [1],
                                       "gamma": [0.1]},
                   use_gridsearch = 'yes',
                   refit = 'yes',
                   refit_iter = 20,
                   use_saved_model = 'no',
                   save_model = 'no',
                   to_plot ='yes',
                   random_seed = 500):


    if use_gridsearch == 'yes':

        # Create model object
        model = GridSearchCV(xgboost.XGBClassifier(), parameters, cv=3, verbose=10, scoring = 'roc_auc')

        # Fit the model
        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1), train['click'])

        # View best hyperparameters
        print('Saved Model Max Depth:', model.best_estimator_.get_params()['max_depth'])
        print('Saved Model Learning Rate:', model.best_estimator_.get_params()['learning_rate'])
        print('Saved Model Sub Sample:', model.best_estimator_.get_params()['subsample'])
        print('Saved Model Colsample By Trees:', model.best_estimator_.get_params()['colsample_bytree'])
        print('Saved Model Reg Alpha:', model.best_estimator_.get_params()['reg_alpha'])
        print('Saved Model Lambda:', model.best_estimator_.get_params()['reg_lambda'])
        print('Saved Model Gamma:', model.best_estimator_.get_params()['gamma'])



        if refit == 'yes':

            # If refit, run
            model = xgboost.XGBClassifier(max_depth=model.best_estimator_.get_params()['max_depth']
                                          , learning_rate=model.best_estimator_.get_params()['learning_rate']
                                          , subsample=model.best_estimator_.get_params()['subsample']
                                          , colsample_bytree=model.best_estimator_.get_params()['colsample_bytree']
                                          , reg_alpha=model.best_estimator_.get_params()['reg_alpha']
                                          , reg_lambda=model.best_estimator_.get_params()['reg_lambda']
                                          , gamma=model.best_estimator_.get_params()['gamma']
                                          , n_estimators=refit_iter
                                          , n_jobs=3
                                          , verbose=10
                                          , random_state = random_seed
                                          , silent=False)

            # Refit
            model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1), train['click'])

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

        else:
            prediction = model.best_estimator_.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

    elif use_saved_model == 'yes':

        # Load from saved files
        model_filename = os.getcwd() + "/models/xgb_model.pkl"
        saved_model = joblib.load(model_filename)

        # View saved model hyperparameters
        print('Saved Model Max Depth:', saved_model.get_params()['max_depth'])
        print('Saved Model Learning Rate:', saved_model.get_params()['learning_rate'])
        print('Saved Model Sub Sample:', saved_model.get_params()['subsample'])
        print('Saved Model Colsample By Trees:', saved_model.get_params()['colsample_bytree'])
        print('Saved Model Reg Alpha:', saved_model.get_params()['reg_alpha'])
        print('Saved Model Lambda:', saved_model.get_params()['reg_lambda'])
        print('Saved Model Gamma:', saved_model.get_params()['gamma'])


        if refit == 'yes':

            # If refit, run
            model = xgboost.XGBClassifier(max_depth=saved_model.get_params()['max_depth']
                                   , learning_rate=saved_model.get_params()['learning_rate']
                                   , subsample=saved_model.get_params()['subsample']
                                          , colsample_bytree=saved_model.get_params()['colsample_bytree']
                                          , reg_alpha=saved_model.get_params()['reg_alpha']
                                          , reg_lambda=saved_model.get_params()['reg_lambda']
                                          , gamma=saved_model.get_params()['gamma']
                                          , n_estimators=refit_iter
                                   , n_jobs=3
                                   , verbose=10
                                          , random_state=random_seed,
                                          silent=False)
            # Fit the model
            model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1), train['click'])

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

        else:
            prediction = saved_model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))
            model = saved_model

    else:

        # Fit the model
        model = xgboost.XGBClassifier(max_depth=parameters['max_depth']
                                      , learning_rate=parameters['learning_rate']
                                      , subsample=parameters['subsample']
                                      , colsample_bytree=parameters['colsample_bytree']
                                      , reg_alpha=parameters['reg_alpha']
                                      , reg_lambda=parameters['reg_lambda']
                                      , gamma=parameters['gamma']
                                      , n_estimators=refit_iter
                                      , n_jobs=3
                                      , verbose=10
                                      , random_state=random_seed
                                      , silent=False)

        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1), train['click'])
        prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

    # Print scores
    print("AUC: %0.5f for XGBoost Model"% (roc_auc_score(validation['click'], prediction[:, 1])))

    # Whether to save the model
    if save_model == 'yes':

        print('Saving the gradient boosted tree model to the disc.')
        model_filename = os.getcwd() + "/models/xgb_model.pkl"
        joblib.dump(model, model_filename, compress=9)

    if to_plot == 'yes':

        plot_ROC_curve(validation['click'], prediction[:, 1])

    return model, prediction[:,1]


# --- SUPPORT VECTOR MACHINES
def support_vector_machine(train, validation,
                           parameters={'C': [0.1, 1, 2],
                                       "kernel": ['linear', 'poly', 'rbf', 'sigmoid'],
                                       "degree": [2, 3, 4],
                                       "gamma": ['auto'],
                                       "tol": [0.001],
                                       "max_iter": [10],
                                       "probability": [True],
                                       "cache_size": [1000]},
                   use_gridsearch = 'yes',
                   refit = 'yes',
                   refit_iter = 20,
                   use_saved_model = 'no',
                   save_model = 'yes',
                   to_plot ='yes',
                   random_seed = 500):


    if use_gridsearch == 'yes':

        # Create model object
        model = GridSearchCV(svm.SVC(), parameters, cv=3, verbose=10, scoring = 'roc_auc')

        # Fit the model
        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1), train['click'])

        # View best hyperparameters
        print('Saved Model C:', model.best_estimator_.get_params()['C'])
        print('Saved Kernel:', model.best_estimator_.get_params()['kernel'])

        if refit == 'yes':

            # If refit, run
            model = svm.SVC(C=model.best_estimator_.get_params()['C']
                                          , kernel=model.best_estimator_.get_params()['kernel']
                                          , degree=model.best_estimator_.get_params()['degree']
                                          , gamma=model.best_estimator_.get_params()['gamma']
                                          , tol=model.best_estimator_.get_params()['tol']
                                          , max_iter=refit_iter
                                          , verbose=10
                                , random_state = random_seed
                            ,probability=True)

            # Refit
            model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1), train['click'])

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

        else:
            prediction = model.best_estimator_.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

    elif use_saved_model == 'yes':

        # Load from saved files
        model_filename = os.getcwd() + "/models/svm_model.pkl"
        saved_model = joblib.load(model_filename)

        # View saved model hyperparameters
        print('Saved Model C:', saved_model.get_params()['C'])
        print('Saved Kernel:', saved_model.get_params()['kernel'])

        if refit == 'yes':

            # If refit, run
            model = svm.SVC(C=saved_model.get_params()['C']
                                          , kernel=saved_model.get_params()['kernel']
                                          , degree=saved_model.get_params()['degree']
                                          , gamma=saved_model.get_params()['gamma']
                                          , tol=saved_model.get_params()['tol']
                                          , max_iter=refit_iter
                                          , verbose=10
                            ,random_state = random_seed
                            ,probability=True)
            # Fit the model
            model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1), train['click'])

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

        else:
            prediction = saved_model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))
            model = saved_model

    else:

        # Fit the model
        model = svm.SVC(C=parameters['C']
                                      , kernel=parameters['kernel']
                                      , degree=parameters['degree']
                                      , gamma=parameters['gamma']
                                      , tol=parameters['tol']
                                      , max_iter=refit_iter
                                      , verbose=10
                        , random_state=random_seed
                        , probability=True)

        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1), train['click'])
        prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

    # Print scores
    print("AUC: %0.5f for SVM Model"% (roc_auc_score(validation['click'], prediction[:, 1])))

    # Whether to save the model
    if save_model == 'yes':

        print('Saving the support vector machines to the disc.')
        model_filename = os.getcwd() + "/models/svm_model.pkl"
        joblib.dump(model, model_filename, compress=9)

    if to_plot == 'yes':

        plot_ROC_curve(validation['click'], prediction[:, 1])

    return model, prediction[:,1]


# --- NAIVE BAYES
def naive_bayes(train, validation, use_saved_model='yes', save_model='yes', to_plot ='yes'):

    if use_saved_model == 'yes':

        # Load from saved files
        model_filename = os.getcwd() + "/models/nb_model.pkl"
        saved_model = joblib.load(model_filename)

        # Make prediction
        prediction = saved_model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

    else:

        # Fit the model
        model = GaussianNB()
        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1), train['click'])

        # Make prediction
        prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

    # Print scores
    print("AUC: %0.5f for Naive Bayes."% (roc_auc_score(validation['click'], prediction[:, 1])))

    # Whether to save the model
    if save_model == 'yes':

        print('Saving the Naive Bayes model to the disc.')
        model_filename = os.getcwd() + "/models/nb_model.pkl"
        joblib.dump(model, model_filename, compress=9)

    if to_plot == 'yes':

        plot_ROC_curve(validation['click'], prediction[:, 1])

    return model, prediction[:,1]

# naive_bayes(train2, validation1, to_plot ='yes')

# --- KNN
def KNN(train, validation,
                           parameters={'n_neighbors': [1, 2,3],
                                       "algorithm": ['auto']},
                   use_gridsearch = 'yes',
                   refit = 'yes',
                   use_saved_model = 'no',
                   saved_model = [],
                   to_plot ='yes',
                   random_seed = 500):


    if use_gridsearch == 'yes':

        # Create model object
        model = GridSearchCV(KNeighborsClassifier(), parameters, cv=3, verbose=10, scoring = 'roc_auc')

        # Fit the model
        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1), train['click'])

        # View best hyperparameters
        print('Best Model N Neighbours:', model.best_estimator_.get_params()['n_neighbors'])
        print('Best Algorithm:', model.best_estimator_.get_params()['algorithm'])

        if refit == 'yes':

            # If refit, run
            model = KNeighborsClassifier(n_neighbors=model.best_estimator_.get_params()['n_neighbors']
                                          , algorithm=model.best_estimator_.get_params()['algorithm'],
                                         n_jobs = 3
                                          , verbose=10)

            # Refit
            model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1), train['click'])

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

        else:
            prediction = model.best_estimator_.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

    elif use_saved_model == 'yes':

        # View saved model hyperparameters
        print('Saved Model N Neighbours:', saved_model.get_params()['n_neighbors'])
        print('Saved Algorithm:', saved_model.get_params()['algorithm'])

        if refit == 'yes':

            # If refit, run
            model = KNeighborsClassifier(n_neighbors=saved_model.get_params()['n_neighbors']
                                         , algorithm=saved_model.get_params()['algorithm'],
                                         n_jobs=3
                                         , verbose=10)
            # Fit the model
            model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1), train['click'])

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

        else:
            prediction = saved_model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))
            model = saved_model

    else:

        # Fit the model
        model = KNeighborsClassifier(n_neighbors=parameters['n_neighbors']
                                     , algorithm=parameters['algorithm'],
                                     n_jobs=3
                                     , verbose=10)


        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1), train['click'])
        prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1))

    # Print scores
    print("AUC: %0.5f for KNN Model"% (roc_auc_score(validation['click'], prediction[:, 1])))

    if to_plot == 'yes':

        plot_ROC_curve(validation['click'], prediction[:, 1])

    return model, prediction[:,1]


# --- FIELD-AWARE FACTORIZATION MACHINE
def factorization_machine(train, validation,
                           parameters={'init_stdev': [0.1],
                                       "rank": [2, 3, 4],
                                       'l2_reg_w': [0.1, 1, 2],
                                       'l2_reg_V':[0.1, 0.5, 1],
                                       'n_iter': [10]},
                  # use_gridsearch = 'yes',
                   refit = 'yes',
                          refit_iter = 20,
                   use_saved_model = 'no',
                   save_model = 'yes',
                   to_plot ='yes',
                   random_seed = 500):

    # Transform the data to sparse representation
    train_X = train.drop(['click', 'bidprice', 'payprice'], axis=1)
    sparse_train_X = sp.csc_matrix(train_X)
    train_Y = train['click']
    train_Y[train_Y == 0] = -1

    validation_X = validation.drop(['click', 'bidprice', 'payprice'], axis=1)
    validation_Y = validation['click']
    validation_Y[validation_Y == 0] = -1
    sparse_validation_X = sp.csc_matrix(validation_X)

    if use_saved_model == 'yes':


        model_filename = os.getcwd() + "/models/fm_model.pkl"
        saved_model = joblib.load(model_filename)

        # View saved model hyperparameters
        print('Saved Model Rank:', saved_model.get_params()['rank'])
        print('Saved Model L2 Regularisation Parameter W:', saved_model.get_params()['l2_reg_w'])
        print('Saved Model L2 Regularisation Parameter V:', saved_model.get_params()['l2_reg_V'])

        if refit == 'yes':

            # If refit, run
            model = als.FMClassification(rank=saved_model.get_params()['rank']
                                          , l2_reg_w=saved_model.get_params()['l2_reg_w']
                                         , l2_reg_V = saved_model.get_params()['l2_reg_V'],
                                         n_iter = refit_iter,
                                         random_state = random_seed)

            model = model.fit(sparse_train_X, train_Y)

            # Make prediction
            prediction = model.predict_proba(sparse_validation_X)

        else:
            prediction = saved_model.predict_proba(sparse_validation_X)
            model = saved_model

    else:

        # Fit the model
        model = als.FMClassification(rank=parameters['rank']
                                     , l2_reg_w=parameters['l2_reg_w']
                                     , l2_reg_V=parameters['l2_reg_V'],
                                     n_iter=parameters['n_iter'],
                                     random_state=random_seed)

        model = model.fit(sparse_train_X, train_Y)
        prediction = model.predict_proba(sparse_validation_X)

    # Print scores
    print("AUC: %0.5f for Factorization Machine Model"% (roc_auc_score(validation_Y, prediction)))

    # Whether to save the model
    if save_model == 'yes':

        print('Saving the Factorization Machine model to the disc.')
        model_filename = os.getcwd() + "/models/fm_model.pkl"
        joblib.dump(model, model_filename, compress=9)

    if to_plot == 'yes':

        plot_ROC_curve(validation_Y, prediction)

    return model, prediction


# --- NEURAL NETWORK
def neural_network(train, validation,
                           parameters={'learning_rate': [0.005, 0.01],
                                       "learning_momentum": ['0.9'],
                                       "regularize": ['L2'],
                                       "dropout_rate": [0.2],
                                       "batch_size": [1],
                                       "n_stable": [10],
                                       "n_iter": [10],
                                       'hidden0__units': [32, 64],
                                       'hidden0__type': ["Rectifier"]},
                   use_gridsearch='yes',
                   refit='yes',
                   refit_iter=20,
                   use_saved_model='no',
                   save_model='yes',
                   to_plot='yes',
                   random_seed=500):

    if use_gridsearch == 'yes':

        # Create layers object
        nn_layers = [Layer("Rectifier", units=64), Layer("Softmax")]

        # Create model object
        model = GridSearchCV(sknn.mlp.Classifier(layers=nn_layers, random_state=random_seed),
                             parameters, cv=3, verbose=10, scoring='roc_auc')

        # Fit the model
        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1).values, train['click'].values)

        # View best hyperparameters
        print('Saved Model Learning Rate:', model.best_estimator_.get_params()['learning_rate'])
        print('Saved Model Dropout Rate:', model.best_estimator_.get_params()['dropout_rate'])
        print('Saved Model Batch Size:', model.best_estimator_.get_params()['batch_size'])
        print('Saved Model Hidden Architecture:', model.best_estimator_.get_params()['layers'])
        print('Saved Model Learning Momentum:', model.best_estimator_.get_params()['learning_momentum'])

        if refit == 'yes':

            # If refit, run
            model = sknn.mlp.Classifier(layers=model.best_estimator_.get_params()['layers']
                                          , learning_rate=model.best_estimator_.get_params()['learning_rate']
                                        , learning_momentum=model.best_estimator_.get_params()['learning_momentum']
                                        , dropout_rate=model.best_estimator_.get_params()['dropout_rate']
                                          , batch_size=model.best_estimator_.get_params()['batch_size']
                                          , n_iter=refit_iter
                                          , verbose=10
                                , random_state = random_seed)

            # Refit
            model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1).values, train['click'].values)

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1).values)

        else:
            prediction = model.best_estimator_.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1).values)

    elif use_saved_model == 'yes':

        # Load from saved files
        model_filename = os.getcwd() + "/models/nn_model.pkl"
        saved_model = joblib.load(model_filename)

        # View saved model hyperparameters
        print('Saved Model Learning Rate:', saved_model.get_params()['learning_rate'])
        print('Saved Model Dropout Rate:', saved_model.get_params()['dropout_rate'])
        print('Saved Model Batch Size:', saved_model.get_params()['batch_size'])
        print('Saved Model Hidden Architecture:', saved_model.get_params()['layers'])
        print('Saved Model Learning Momentum:', saved_model.get_params()['learning_momentum'])

        if refit == 'yes':

            # If refit, run
            model = sknn.mlp.Classifier(layers=saved_model.get_params()['layers']
                                          , learning_rate=saved_model.get_params()['learning_rate']
                                        , learning_momentum=saved_model.get_params()['learning_momentum']
                                        , dropout_rate=saved_model.get_params()['dropout_rate']
                                          , batch_size=saved_model.get_params()['batch_size']
                                          , n_iter=refit_iter
                                          , verbose=10
                                , random_state = random_seed)

            # Fit the model
            model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1).values, train['click'].values)

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1).values)

        else:
            prediction = saved_model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1).values)
            model = saved_model

    else:

        # Fit the model
        model = sknn.mlp.Classifier(layers=parameters['layers']
                                    , learning_rate=parameters['learning_rate']
                                    , learning_momentum=parameters['learning_momentum']
                                    , dropout_rate=parameters['dropout_rate']
                                    , batch_size=parameters['batch_size']
                                    , n_iter=refit_iter
                                    , verbose=10
                                    , random_state=random_seed)

        model = model.fit(train.drop(['click','bidprice', 'payprice'], axis=1).values, train['click'].values)
        prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1).values)

    # Print scores
    print("AUC: %0.5f for Neural Network Model"% (roc_auc_score(validation['click'], prediction[:, 1])))

    # Whether to save the model
    if save_model == 'yes':

        print('Saving the neural network to the disc.')
        model_filename = os.getcwd() + "/models/nn_model.pkl"
        joblib.dump(model, model_filename, compress=9)

    if to_plot == 'yes':

        plot_ROC_curve(validation['click'], prediction[:, 1])

    return model, prediction[:,1]


# --- STACKING
def stacking_classifier(train, validation, refit = 'yes', use_saved_model = 'no', save_model = 'yes', to_plot ='yes',
                        meta_leaner_parameters={'max_depth':20, "n_estimators":20, "learning_rate":0.05,
                                                'silent':False, 'n_jobs':3,'subsample':1, 'objective':'binary:logistic',
                                                'colsample_bytree':1, 'eval_metric':"auc", 'reg_alpha':0.1,
                                                'reg_lambda':0.1, 'random_state':500},
                        stacking_cv_parameters={'use_probas': False,
                                               'use_features_in_secondary': True,
                                               'cv': 5,
                                               'store_train_meta_features': True,
                                               'refit': True}):

    if use_saved_model == 'no':

        # Import all the grid searched models

        # Logistic
        model_filename = os.getcwd() + "/models/logistic_model.pkl"
        log_model = joblib.load(model_filename)

        # Random Forest
        model_filename = os.getcwd() + "/models/rf_model.pkl"
        rf_model = joblib.load(model_filename)

        # Extreme Random Forest
        model_filename = os.getcwd() + "/models/erf_model.pkl"
        erf_model = joblib.load(model_filename)

        # XGBoost
        model_filename = os.getcwd() + "/models/xgb_model.pkl"
        xgb_model = joblib.load(model_filename)

        # SVM
        model_filename = os.getcwd() + "/models/svm_model.pkl"
        svm_model = joblib.load(model_filename)

        # Naive Bayes
        model_filename = os.getcwd() + "/models/nb_model.pkl"
        nb_model = joblib.load(model_filename)

        # Neural Network
        model_filename = os.getcwd() + "/models/nn_model.pkl"
        nn_model = joblib.load(model_filename)

        meta_learner = xgboost.XGBClassifier(max_depth=meta_leaner_parameters['max_depth'],
                                             n_estimators=meta_leaner_parameters['n_estimators'],
                                             learning_rate=meta_leaner_parameters['learning_rate'],
                                             silent=meta_leaner_parameters['silent'],
                                             n_jobs=meta_leaner_parameters['n_jobs'],
                                             subsample=meta_leaner_parameters['subsample'],
                                             objective=meta_leaner_parameters['objective'],
                                             colsample_bytree=meta_leaner_parameters['colsample_bytree'],
                                             eval_metric=meta_leaner_parameters['eval_metric'],
                                             reg_alpha=meta_leaner_parameters['reg_alpha'],
                                             reg_lambda=meta_leaner_parameters['reg_lambda'],
                                             random_state = meta_leaner_parameters['random_state'])

        model = StackingCVClassifier(classifiers=[rf_model, erf_model, xgb_model],
                                    meta_classifier=meta_learner, use_probas=stacking_cv_parameters['use_probas'],
                                    use_features_in_secondary = stacking_cv_parameters['use_features_in_secondary'],
                                    store_train_meta_features=stacking_cv_parameters['store_train_meta_features'],
                                    cv = stacking_cv_parameters['cv'])

        model = model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1).values, train['click'].values)
        prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1).values)

    else:

        # Load from saved files
        model_filename = os.getcwd() + "/models/stacked_model.pkl"
        saved_model = joblib.load(model_filename)

        if refit == 'yes':

            # If refit, run
            model = saved_model.fit(train.drop(['click', 'bidprice', 'payprice'], axis=1).values, train['click'].values)

            # Make prediction
            prediction = model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1).values)

        else:
            prediction = saved_model.predict_proba(validation.drop(['click', 'bidprice', 'payprice'], axis=1).values)
            model = saved_model


    # Whether to save the model
    if save_model == 'yes':

        print('Saving the stacked model to the disc.')
        model_filename = os.getcwd() + "/models/stacked_model.pkl"
        joblib.dump(model, model_filename, compress=9)


    # Print scores
    print("AUC: %0.5f for Stacking Model"% (roc_auc_score(validation['click'], prediction[:, 1])))

    if to_plot == 'yes':

        plot_ROC_curve(validation['click'], prediction[:, 1])

    return model, prediction[:,1]

####################### END ########################