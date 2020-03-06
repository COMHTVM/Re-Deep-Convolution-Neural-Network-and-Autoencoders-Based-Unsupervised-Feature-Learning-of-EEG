from os.path import join
from pathlib import Path
from zipfile import ZipFile

from bs4 import BeautifulSoup
from numpy import zeros, ones, concatenate, array, reshape, isin
from pandas import DataFrame
from pandas import read_csv
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from wget import download

# TODO: evite de usar import *, seja especifico sobre quais funcoes ira buscar para ficar facil entender de onde vieram as funcoes dos codigos
from autoenconder import *


def zip_with_unique(base, list_suffix):
    """ Auxiliary function to generate a paired 
    list considering a unique element.
    
    An adaptation of the convolution function (`zip`) 
    to map a single value in a sequence tuple.  
    This mapping is a surjective-only.

    An adaptation of the "scalar product" 
    to make a zip with vectors of different sizes. 
    The first vector must have 1 item, 
    while the second must-have n items.
    
    Parameters
    ----------
    base: array-like, shape (1, )
        One (1) base prefix that will be paired with the suffixes.
        
    list_suffix : array-like, shape (n_suffix,)
        A suffix list that will be paired with one prefix.
    
    Returns
    -------
    list: array-like, shape (n_suffix)
        Base added with the suffix.
    """

    return list(base + suffix for suffix in list_suffix)

# TODO: Nao misture diferentes docstring em um unico projeto.
def download_bonn(path_data='data/boon/') -> [str]:
    """
    Adapted from mne-tools.github.io/mne-features/auto_examples/plot_seizure_example.html
    Code changes were:
        * Adding more folders;
        * Control for folder creation;

    Parameters
    ----------
    path_data

    Returns
    -------

    """
    fold = Path(path_data)
    child_fold = ['setA', 'setB', 'setC', 'setD', 'setE']
    base_url = 'http://epileptologie-bonn.de/cms/upload/workgroup/lehnertz/'
    urls_suffix = ['Z.zip', 'O.zip', 'N.zip', 'F.zip', 'S.zip']

    path_child_fold = zip_with_unique(path_data, child_fold)

    if fold.exists():
        print("Folder already exists")
        check_child_folders = [Path(child).exists()
                               for child in path_child_fold]

        if all(check_child_folders):
            print("Subfolders already exist")

            return path_child_fold
    else:
        print("Creating folder")
        # Create parent directory
        fold.mkdir(parents=True, exist_ok=True)
        # This way, the child directory will also be created.
        for child in path_child_fold:
            Path(child).mkdir(parents=True, exist_ok=True)

        urls = zip_with_unique(base_url, urls_suffix)

        print("Downloading and unzipping the files")

        for url, path in list(zip(urls, path_child_fold)):
            file_directory = download(url, path)

            with ZipFile(file_directory, "r") as zip_ref:
                zip_ref.extractall(path)

    return path_child_fold

def download_item(url_base, name_base, page=True):
    download(url_base, name_base)
    if (page):
        base = open(name_base, "r").read()
        soup = BeautifulSoup(base, 'html.parser')
        return filter_list([link.get('href') for link in soup.find_all('a')])


def filter_list(folders_description):
    listchb = ['chb' + str(i) + '/' for i in range(11, 25)]
    listchb.append('../')

    return [item for item in folders_description if ~isin(item, listchb)]


def get_folders(folders_description):
    return [item for item in folders_description if item.find('/') != -1]


def get_files(folders_description):
    return [item for item in folders_description if item.find('/') == -1]


def download_chbmit(url_base, path_save):
    """ 
    
    Parameters
    ----------
    url_base : 
        
    path_save : 
    
    Returns
    -------
    """
    # TODO: Se estiver usando python 3.6+, considere usar f-strings
    #  Senao, procure se habituar com o .format
    #  https://realpython.com/python-f-strings/
    print("Downloading the folder information: " + path_save)
    fold_save = Path(path_save)

    if (~fold_save.exists()):
        fold_save.mkdir(parents=True, exist_ok=True)

        folders_description = download_item(url_base, path_save + 'base.html', page=True)

        folders = get_folders(folders_description)
        description = get_files(folders_description)

        patient_url = zip_with_unique(url_base, folders)
        patient_item = zip_with_unique(path_save, folders)
        description_base = zip_with_unique(url_base, description)

        # TODO: Se estiver usando python 3.6+, considere usar f-strings
        #  Senao, procure se habituar com o .format
        #  https://realpython.com/python-f-strings/
        print("Downloading the folder files: " + path_save)
        for item, name in zip(description_base, description):
            download_item(item, path_save + name, page=False)

        for item, name in zip(patient_url, patient_item):
            download_chbmit(item, name)
    else:
        print("Folder already exists\n Use load_dataset_chbmit")

    return patient_item


def load_dataset_boon(path_child_fold) -> array:
    """Function for reading the boon database, and return X and y.
    Also adapted from:
    https://mne-tools.github.io/mne-features/auto_examples/plot_seizure_example.html
    Parameters
    ----------

    path_child_fold : TO-DO

    Returns
    -------
    X : array-like, shape (n_samples, n_features)
        Data vectors, where n_samples is the number of samples
        and n_features is the number of features.
    y : array-like, shape (n_samples,)
        Target values.

    """

    data_segments = list()
    labels = list()

    for path in path_child_fold:

        f_names = [s for s in Path(path).iterdir() if str(s).lower().endswith('.txt')]

        for f_name in f_names:
            _data = read_csv(f_name, sep='\n', header=None)

            data_segments.append(_data.values.T[None, ...])

        if ('setE' in path) or ('setC' in path) or ('setD' in path):

            labels.append(ones((len(f_names),)))
        else:
            labels.append(zeros((len(f_names),)))

    X = concatenate(data_segments).squeeze()
    y = concatenate(labels, axis=0)

    return X, y


def preprocessing_split(X, y, test_size=.20, random_state=42) -> [array]:
    """Function to perform the train and test split 
    and normalize the data set with Min-Max.
    
    Parameters
    ----------
        
    X : array-like, shape (n_samples, n_features)
        Training vectors, where n_samples is the number of samples
        and n_features is the number of features.
        
    y : array-like, shape (n_samples,)
        Target values.
    
    test_size : float
        value between 0 and 1 to indicate the 
        percentage that will be used in the test.
    
    random_state : int
        seed to be able to replicate split
        
    Returns
    -------
    
    TO-DO: Explanation that will be 
    the separation between training and testing.


    """

    X_train, X_test, Y_train, Y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state)

    # TODO: evite diferentes padroes para nomes de variaveis.
    # MinMax Scaler
    minMax = MinMaxScaler()
    minMax = minMax.fit(X_train)

    X_train = minMax.transform(X_train)
    X_test = minMax.transform(X_test)

    X_train = X_train[:, :4096]
    X_test = X_test[:, :4096]

    X_train = reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
    X_test = reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

    return X_train, X_test, Y_train, Y_test

#  TODO: Nao use nomes em maiusculo para variaveis, e sim para constantes.
def build_featureDataSet(X_train, X_test,
                         Y_train, Y_test,
                         PATH_DATASET, EPOCHS,
                         BATCH, type_loss,
                         value_encoding_dim):
    """

    Parameters
    ----------
    X_train
    X_test
    Y_train
    Y_test
    PATH_DATASET
    EPOCHS
    BATCH
    type_loss
    value_encoding_dim

    Returns
    -------

    """
    # TODO: Se estiver usando python 3.6+, considere usar f-strings
    #  Senao, procure se habituar com o .format
    #  https://realpython.com/python-f-strings/
    print("Convert and save with value enconding dimension: {}".format(value_encoding_dim)
          
          
    X_train_encode, X_test_encode, autoEncoder_ = feature_learning(epochs=EPOCHS, batch_size=BATCH,
                                                                   name_dataset=PATH_DATASET,
                                                                   X_train=X_train, X_test=X_test,
                                                                   type_loss=type_loss,
                                                                   value_encoding_dim=value_encoding_dim)
    df_train = DataFrame(X_train_encode)
    df_train.columns = df_train.columns.astype(str)
    df_train['class'] = Y_train

    df_test = DataFrame(X_test_encode)
    df_test.columns = df_test.columns.astype(str)
    df_test['class'] = Y_test

    path_train, path_test = save_featureDataSet(df_train=df_train,
                                                df_test=df_test,
                                                value_encoding_dim=value_encoding_dim,
                                                PATH_DATASET=PATH_DATASET, type_loss=type_loss)

    return autoEncoder_, path_train, path_test


def save_feature(df_train, df_test, value_encoding_dim,
                        PATH_DATASET, type_loss) -> [str]:
    """

    Parameters
    ----------
    df_train
    df_test
    value_encoding_dim
    PATH_DATASET
    type_loss

    Returns
    -------

    """
          
    # Join pathname between a string that contains the base  
    # pathname dataset and a folder called feature_learning, 
    # which will be created to save the latent spaces 
    # generated by AutoEnconder.          
    path_save = join(PATH_DATASET, 'feature_learning')
          
    # Conversion of the pathname string to the class PurePath,
    # To use the class to create a folder 
    # on the system if it doesn't exist.
    fold_save = Path(path_save)

    #       
          
    prefix_name_train = 'train_{}_{}.parquet'.format(value_encoding_dim, 
                                                     type_loss)

    prefix_name_test  = 'test_{}_{}.parquet'.format(value_encoding_dim, 
                                                    type_loss)

    save_train_name   = join(path_save, prefix_name_train)
    save_test_name    = join(path_save, prefix_name_test)

    if (~fold_save.exists()):
          
        fold_save.mkdir(parents=True, exist_ok=True)

    df_train.to_parquet(save_train_name, engine='pyarrow')

    df_test.to_parquet(save_test_name, engine='pyarrow')

    return save_train_name, save_test_name
