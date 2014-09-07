from abacuspb import app

def runserver(debug):
    app.run(debug=debug, host='127.0.0.1', port=5000)
    
if __name__ == '__main__':
    runserver(debug=True)