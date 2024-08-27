def return_convert_type(result, return_type):
    if return_type == 'pt':
        return result
    elif return_type == 'np':
        return result.cpu().numpy()
    elif return_type == 'ls':
        return result.cpu().numpy().tolist()
    else:
        raise ValueError(f"return_type should be 'pt', 'np' or 'ls', but got {return_type}")