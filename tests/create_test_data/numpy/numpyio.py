import numpy as np 

def main():
    a = np.arange(24).reshape(3,8)
    
    np.save("range.3x8.npy", a)
    
    x = np.arange(10)
    y = np.sin(x)
    d = ['a', {5: '5'}]
    np.savez('sinx.npz', x=x, y=y, d=d)
    np.savez('d.npz', d)

if __name__ == "__main__":
    main()
    
    