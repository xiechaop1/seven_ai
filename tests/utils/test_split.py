def get_required_length(count: int) -> int:
            if count == 0:
                return 0  
            return 10 * (3 ** (count - 1)) 

if __name__ == "__main__":
    for i in range(10):
        print(i,get_required_length(i))
