import time

def distance_moving(A,va,B,vb,t):
    A = A + t*va
    B = B + t*vb
    distance(A + t*va,B + t*vb,t)
    

def distance(A,B,t):
    sum = 0
    for i in range(3):
        cal = (A[i] - B[i])**2
        sum = sum + cal
    dist = sum ** 0.5
    print("Distance is at", t ," : ", dist)

def main():
    A = [100,200,305]
    B = [500,356,586]

    va = [2,2,8]
    vb = [8,5,6]
    for t in range(10):
        distance_moving(A,va,B,vb,t)

main()