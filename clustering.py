from KarmaLego import *
from collections import Counter
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram
from scipy.cluster.hierarchy import linkage as HierarchicalClustering


def prepare_matrix(tree_filename, num_of_patients):
    """
    Prepare matrix of data where each row is a vector representing one patient.
    Shape: (number of patients, number of TIRPs)

    :param tree_filename: name of the file where tree of TIRPs is saved
    :param num_of_patients: number of patients in entity list, from which tree of TIRPs was constructed
    :return: 2D np.array
    """
    tree = load_pickle(tree_filename)
    all_nodes = tree.find_tree_nodes([])

    mat = np.zeros((num_of_patients, len(all_nodes)))
    for i, tirp in enumerate(all_nodes):
        tirp_size = len(tirp.symbols)
        mat[tirp.entity_indices_supporting, i] = 1 / tirp_size
    return mat


def hierarchical_clustering_dendrogram(mat, metric, linkage):
    """
    Run hierarchical clustering on data matrix mat. Show truncated dendrogram.

    :param mat: matrix of input data, shape: (number of patients, number of TIRPs)
    :param metric: distance metric to use
    :param linkage: type of linkage to use
    :return: None
    """
    Z = HierarchicalClustering(mat, method=linkage, metric=metric)
    dendrogram(Z, p=5, truncate_mode='level')
    plt.xlabel('index of patient in entity list')
    plt.ylabel('distance')
    plt.title('Trucated dendrogram using %s linkage and %s metric' % (linkage, metric))
    plt.show()


def hierarchical_clustering(mat, k, metric, linkage):
    """
    Run hierarchical clustering on data matrix mat and find k clusters using specified metric and linkage.

    :param mat: matrix of input data, shape: (number of patients, number of TIRPs)
    :param k: number of clusters
    :param metric: distance metric to use
    :param linkage: type of linkage to use
    :return: list of labels (len = number of patients), each label is a cluster that patient belongs to
    """
    return AgglomerativeClustering(n_clusters=k, affinity=metric, linkage=linkage).fit_predict(mat)


def k_means(mat, k):
    """
    Run k-means algorithm on data matrix mat and find k clusters.

    :param mat: matrix of input data, shape: (number of patients, number of TIRPs)
    :param k: number of clusters
    :return: list of labels (len = number of patients), each label is a cluster that patient belongs to
    """
    return KMeans(n_clusters=k, max_iter=1000).fit_predict(mat)


def pca(mat, num_of_components):
    """
    Run PCA decomposition on data matrix.

    :param mat: matrix of input data, shape: (number of patients, number of TIRPs)
    :param num_of_components: number of components wanted after PCA
    :return: 2D np.array of shape (number of patients, num_of_components)
    """
    return PCA(n_components=num_of_components).fit_transform(mat)


def visualize_clusters_in_2D(mat, labels, algorithm_name, annotations, show_annotations=False, share_of_shown=1.0):
    """
    Visualize clusters after performing PCA to get 2D points.

    :param mat: matrix of input data, shape: (number of patients, number of TIRPs)
    :param labels: list of labels (len(labels) = number of patients), each label is a cluster that patient belongs to
    :param algorithm_name: name of the clustering algorithm
    :param annotations: list of annotations to be plotted next to points, only applicable if show_annotations is True
                        len(labels) = len(annotations)
    :param show_annotations: boolean - determining if annotations (IDs) are showed next to points
    :param share_of_shown: share of annotations to show, should have value in the interval (0, 1],
                           only applicable if show_annotations is True
    :return: None
    """
    pca_mat = pca(mat, 2)
    _, ax = plt.subplots()
    ax.scatter(pca_mat[:, 0], pca_mat[:, 1], c=labels, s=5, cmap='rainbow')
    if show_annotations:
        for i in range(len(labels)):
            if i % round(1 / share_of_shown) == 0:
                ax.annotate(annotations[i], (pca_mat[i, 0], pca_mat[i, 1]), size=8)
    plt.xlabel('x1')
    plt.ylabel('x2')
    plt.title('Each of %d points represents one patient after performing %s clustering and PCA' % (len(labels), algorithm_name))
    plt.show()


if __name__ == "__main__":
    # possible options of use: 'artificial', 'pneumonia', '10%', 'all'
    use = '10%'

    algorithm = 'k-means'  # choose clustering algorithm: 'hierarchical' or 'k-means'
    k = 3  # choose number of clusters wanted

    tree_filename = ''
    num_of_patients = 0
    annotations = []
    if use == 'artificial':
        tree_filename = 'data/artificial_entities_tree.pickle'
        num_of_patients = 4
        annotations = ['Disease ' + str(i) for i in range(1, 5)]
    elif use == 'pneumonia':
        tree_filename = 'data/pneumonia_tree.pickle'
        num_of_patients = len(read_json('data/pneumonia_entity_list.json'))
        annotations = ['Pneumonia'] * num_of_patients
    elif use == '10%':
        # use 10% of all admissions data
        tree_filename = 'data/10percent_all_admissions_tree.pickle'
        num_of_patients = len(read_json('data/10percent_all_admissions_entity_list.json'))
        annotations = ordered_diagnoses4clustering()
    elif use == 'all':
        # all data
        tree_filename = 'data/tree.pickle'
        num_of_patients = len(read_json('data/entity_list.json'))
        annotations = all_ordered_diagnoses4clustering()
        # note: if patient doesn't have diagnosis, his annotation is empty string ''

    if tree_filename:
        mat = prepare_matrix(tree_filename, num_of_patients)

        labels = None
        if algorithm == 'k-means':
            labels = k_means(mat, k)
        elif algorithm == 'hierarchical':
            metric = 'euclidean'
            linkage = 'average'

            labels = hierarchical_clustering(mat, k, metric, linkage)
            hierarchical_clustering_dendrogram(mat, metric, linkage)

        if labels is not None:
            print(Counter(labels))
            visualize_clusters_in_2D(mat, labels, algorithm, annotations, show_annotations=True, share_of_shown=0.001)

