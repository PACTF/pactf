#!/usr/bin/python2


TWODIG_COMB = {}
for i in xrange(1,10):
    for j in xrange(10):
        if i+j <= 9: TWODIG_COMB[(i,j)] = 1

def count_n_bruteforce(m):
    total = 0
    for i in xrange(10**(m-1),10**m):
        s = str(i)
        for j in xrange(m-2):
            if sum(int(c) for c in s[j:j+3]) <= 9: total += 1
    return total

def count_n_test(m):
    arr = [0] * m
    arr[0] = {}
    arr[1] = TWODIG_COMB
    for n in xrange(2, m):
        arr[n] = {}
        for i,j in arr[n-1]:
            for k in xrange(10-i-j):
                if (j,k) in arr[n]:
                    arr[n][(j,k)] += arr[n-1][(i,j)]
                else: arr[n][(j,k)] = arr[n-1][(i,j)]
    return sum(arr[-1].values())

print str(count_n_test(10000))[:15]
