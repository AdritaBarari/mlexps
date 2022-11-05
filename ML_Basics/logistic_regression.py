'''
Author: Adrita Barari
Date of Creation: 27/10/2022
Date Updated: 1/11/2022
ToDo: Explore Batch Gradient Descent, SGC, Mini batch Gradient descenet 
ToDo: Explore different optiizers and Activation functions
ToDo: Add regularization too
With Visualizations
With Test cases
With Logger
'''
#Imports
from sklearn.datasets import make_classification
from config import Config
import numpy as np
from tqdm import tqdm
from matplotlib import pyplot as plt

conf = Config()

class CustomLogisticRegression:

    def __init__(self, num_iters, lr, X_train, y_train, X_test, y_test):
        self.lr = lr
        self.num_iters = num_iters
        self.X_train, self.y_train, self.X_test, self.y_test = X_train, y_train, X_test, y_test


    def _train_model_parameters(self, type='sgd') :           
        A = 1 / ( 1 + np.exp( - ( self.X_train.dot( self.W ) + self.b ) ) )
        # calculate gradients        
        error = ( A - self.y_train.T )  # 
        error = np.reshape( error, self.m )        
        dW = np.dot( self.X_train.T, error ) / self.m         
        db = np.sum( error ) / self.m  
        # update weights    
        self.W = self.W - self.lr * dW    
        self.b = self.b - self.lr * db
        #print('Grad Descent --')

    def train(self, weight_init=None, bias_init=None, display_wts=True):
        '''
        Train Function to update weights
        '''
        #print('shape',X_train.shape)        #print(X_train[0])
        print('I train: X_train,y_train: shapes',self.X_train.shape,self.y_train.shape)
        self.m, self.n = self.X_train.shape[0], self.X_train.shape[1]  #m --No.of samples, n --No. of features
        if weight_init is None:
            #by default initialise to Zeroes
            self.W = np.ones(self.n)  
            self.b = 0
            for iter in tqdm(range(self.num_iters)):
                self._train_model_parameters()
            if display_wts:
                print('Trained Model weights',self.W)
                print('Trained Bias,', self.b)
    
    def predict(self, X_test):
        '''
        
        Y_pred = model.predict( X_test ) 
        y_pred = self.W * x_test + self.b
        true_positives = 0
        accuracy, precision, recall = 0, 0, 0

        if y_pred == y_test:
            correct +=1

        acccuracy = correct/self.m
        '''
        Z = 1 / ( 1 + np.exp( - ( X_test.dot( self.W ) + self.b ) ) )  #Sigmoid Function      
        Y = np.where( Z > 0.4, 1, 0 )        
        return Y


def prepareData(n_samples=200, split_ratio=.8):
    '''
    '''
    X, y = make_classification(n_samples=20, n_features=5, n_repeated=0,n_redundant=0, n_informative=2, random_state=0, class_sep=10)
    
    # Creating the multi-class classification dataset with two informative feature and one cluster per class
    #X, y = make_classification(n_features=2, n_redundant=0, n_informative=2, n_clusters_per_class=1, n_classes=3)

    # Plotting the dataset
    plt.figure(figsize=(7.50, 3.50))
    plt.subplots_adjust(bottom=0.05, top=0.9, left=0.05, right=0.95)
    plt.subplot(111)
    plt.title("Multi-class classification dataset with two informative feature and one cluster per class", fontsize="12")
    plt.scatter(X[:, 0], X[:, 1], marker="x", c=y, s=20, cmap='bwr')
    plt.show()
    train_samples = round(len(X) * split_ratio)
    X_train,y_train,X_test, y_test = X[:train_samples], y[:train_samples], X[train_samples:], y[train_samples:]
    print('X_train,y_train: shapes',X_train.shape,y_train.shape)
    print(X_train[0])
    return X_train,y_train,X_test, y_test


def run():
    '''
    Driver Code for running the Training and Evaluation 
    '''
    X_train,y_train,X_test,y_test = prepareData(200)
    #print(':',len(X_train),':' , len(X_train[0]))   
    custLR = CustomLogisticRegression(conf.NUM_ITERATIONS, conf.LR, X_train, y_train, X_test,y_test)
    custLR.train()
    #print('Trained weight matrix', self.W)  # The weights of the trained model
    #print('trained bias Value',self.b)
    #custLR.eval()
    print('Evaluating on the Test Dataset..')
    # Prediction on test set
    y_pred = custLR.predict( X_test )    
    #Y_pred1 = model1.predict( X_test )
      
    # measure performance    
    correctly_classified = 0    
    #correctly_classified1 = 0
      
    # counter    
    count = 0    
    for count in range( np.size( y_pred ) ) :  
        if y_test[count] == y_pred[count] :            
            correctly_classified = correctly_classified + 1
        #if Y_test[count] == Y_pred1[count] :            
            #correctly_classified1 = correctly_classified1 + 1
        count = count + 1
          
    print( "Accuracy on test set by our model: ", (correctly_classified / count ) * 100 )
    #print( "Accuracy on test set by sklearn model   :  ", ( 
      #correctly_classified1 / count ) * 100 )
    
if __name__=='__main__':

    # Run
    # Prepare Data -Split it into proportions
    # Create Custom Logictic Regression
    # Compare with Scikit Logistic Regression
    # Code the Evalutaion metrics
    # See Visualizations

    run()    