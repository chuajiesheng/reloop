import numpy as np
import scipy.sparse as sp
import LiftedLPWrapper as llp
import pyublas


def eigenBoundsPartition(A,Bcc):
    print "\t lower bound:"
    N = np.linalg.inv(np.dot(Bcc.T,Bcc))
    L = np.dot(N,np.dot(Bcc.T,np.dot(A,Bcc)))
    Q = np.dot(A,Bcc)
    wl = np.linalg.eigvals(L)    
    print "\t",np.sort(wl)[-1]
    print "\t upper bound:"
    
    U = np.zeros_like(L)
    for i in range(Q.shape[1]):
        ind = Bcc[:,i].nonzero()
        for j in range(Q.shape[1]):
#                print "(",i,",",j,"):", Q[ind[0],j]
            U[i,j] = np.max(Q[ind[0],j])
#            Qtmp = Q[ind[0],j]
#            maxind = np.abs(Qtmp).argmax()
##                print maxind
#            U[i,j] = Qtmp[0,maxind]
#        print Q       
#    print np.round(U,2) 
#        print np.round(L,2)
    wu = np.linalg.eigvals(U)  
    print "\t",np.sort(wu)[-1]
    
def kStepEigenBounds(A):
#    A = np.abs(A)
    S = np.sum(A, axis=0)
    print A
#    S = np.tile(S,(A.shape[1],1))
#    print S.shape
#    
#    A = A/S
    n = A.shape[0]
    print "true leading eigenvalue"
    w = np.linalg.eigvalsh(A)
    print np.sort(w)[-1]
    oldk = 0
    for liftiter in range(1,n+2):

        print liftiter,"-step:"  
        bcols = llp.blockMatrixFromDenseArray(A.round(6),np.zeros(n,dtype=float),liftiter);
        k = np.max(bcols) + 1 
        if oldk == k: return
        else: oldk = k
        print "\tsize of matrix: ", k
        brows = np.array(range(n))
        bdata = np.ones(n,dtype=np.int)
        Bcc = sp.coo_matrix((bdata,np.vstack((brows,bcols))),dtype=np.int).todense()
        eigenBoundsPartition(A,Bcc)
#        print wu    


A = np.array([[-4,1,-2],[1,-2,1],[-2,1,1]], dtype=np.float)
print np.linalg.eigvals(A)
B = np.array([[1,0],[1,0],[0,1]])
eigenBoundsPartition(A,B)
kStepEigenBounds(A)

