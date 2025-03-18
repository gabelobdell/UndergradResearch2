def getslice(vars, dims, start, end):
    datslice = vars.sel(time=slice(start, end)).mean(dim=dims)
    return datslice

def getchange(vars, dims, start1, end1, start2, end2):
    period1 = vars.sel(time=slice(start1, end1)).mean(dim=dims)
    period2 = vars.sel(time=slice(start2, end2)).mean(dim=dims)
    return (period2 - period1)