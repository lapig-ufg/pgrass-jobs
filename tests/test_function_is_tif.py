from app.fuctions import is_tif


def test_is_tif():
    assert is_tif('/HOME/FILE.TIF') == True
    assert is_tif('/HOME/FILE.TIFF') == True
    assert is_tif('/HOME/FILE.tif') == True
    assert is_tif('/HOME/FILE.tiff') == True
    assert is_tif('/HOME/FILE.txt') == False
    assert is_tif('https://HOME/FILE.tiff') == True
    assert is_tif('https://HOME/FILE.TIF') == True
    assert is_tif('https://HOME/FILE.txt') == True
    assert is_tif('ftps://HOME/FILE.tiff') == True
    assert is_tif('ftps://HOME/FILE.txt')  == False
    
   
