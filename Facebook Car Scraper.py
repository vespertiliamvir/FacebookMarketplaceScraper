from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime
import csv
from re import sub
from decimal import Decimal





#everything that has the nameOfPreferencesFile in the parameters of the functions are just having to do with maintaining the preferences file, and not the actual program itself

def dictatePreferences(nameOfPreferencesFile):
    print("Okay, here are the new preferences: ")

    with open(nameOfPreferencesFile) as f:
        csvReader = csv.reader(f, delimiter = ',')
        for line in csvReader:
            print(line)

    return

def preferencesReader(nameOfPreferencesFile):



    with open(nameOfPreferencesFile) as f:
        keyOrValue = 0
        keys = []
        values = []
        preferencesDictionary = {}

        csvReader = csv.reader(f, delimiter=',')
        # preferencesDictionary = {}

        for line in csvReader:
            for entry in line:
                if(keyOrValue == 0):
                    keys.append(entry)
                    keyOrValue = 1
                else:
                    values.append(entry)
                    keyOrValue = 0

        for key in keys:
            for value in values:
                preferencesDictionary[key] = value
                values.remove(value)
                break
    return (preferencesDictionary)

def mileageChange(nameOfPreferencesFile):


        preferencesDictionary = preferencesReader(nameOfPreferencesFile)

            # csvWriter.writerow([key,preferencesDictionary[key]])

        print("the current minimum mileage value is: ",preferencesDictionary['Minimum Mileage'])
        print("and the current maximum mileage vlue is: ",preferencesDictionary['Maximum Mileage'])

        minMileage = input("Please enter a new minimum mileage: ")

        while(not( minMileage.isdigit() )):
            minMileage = input("I'm sorry, but "+minMileage+ " is not a valid entry.  Please enter a positive integer value")

        maxMileage = input("Please enter a new maximum Mileage: ")

        while((not( maxMileage.isdigit() )) or (int(maxMileage) < int(minMileage)) ):
            maxMileage = input("I'm sorry, but "+maxMileage+ " is not a valid entry.  Please enter a positive integer value that is larger than the minimum mileage")

        preferencesDictionary['Minimum Mileage'] = minMileage
        preferencesDictionary['Maximum Mileage'] = maxMileage

        return(preferencesDictionary)


def priceChange(nameOfPreferencesFile):
    preferencesDictionary = preferencesReader(nameOfPreferencesFile)

        # csvWriter.writerow([key,preferencesDictionary[key]])

    print("the current minimum price value is: ",preferencesDictionary['Minimum Price'])
    print("and the current maximum price vlue is: ",preferencesDictionary['Maximum Price'])

    minPrice = input("Please enter a new minimum price: ")

    while(not( minPrice.isdigit() )):
        minPrice = input("I'm sorry, but "+minPrice+ " is not a valid entry.  Please enter a positive integer value")

    maxPrice = input("Please enter a new maximum price: ")

    while((not( maxPrice.isdigit() )) or (int(maxPrice) < int(minPrice)) ):
        maxPrice = input("I'm sorry, but "+maxPrice+ " is not a valid entry.  Please enter a positive integer value that is larger than the minimum price")

    preferencesDictionary['Minimum Price'] = minPrice
    preferencesDictionary['Maximum Price'] = maxPrice

    return(preferencesDictionary)

def lengthChange(nameOfPreferencesFile):
    preferencesDictionary = preferencesReader(nameOfPreferencesFile)

        # csvWriter.writerow([key,preferencesDictionary[key]])

    print("the current length value is: ",preferencesDictionary['Scroll Down Length'])

    length = input("Please enter a new length: ")

    while(not( length.isdigit() )):
        length = input("I'm sorry, but "+length+ " is not a valid entry.  Please enter a positive integer value")


    preferencesDictionary['Scroll Down Length'] = length

    return(preferencesDictionary)

def yearChange(nameOfPreferencesFile):
    preferencesDictionary = preferencesReader(nameOfPreferencesFile)

        # csvWriter.writerow([key,preferencesDictionary[key]])

    print("the current minimum year value is: ",preferencesDictionary['Minimum Year'])
    print("and the current maximum year vlue is: ",preferencesDictionary['Maximum Year'])

    minYear = input("Please enter a new minimum year: ")

    while(not( minYear.isdigit() )):
        minYear = input("I'm sorry, but "+minYear+ " is not a valid entry.  Please enter a positive integer value")

    maxYear = input("Please enter a new maximum year: ")

    while((not( maxYear.isdigit() )) or (int(maxYear) < int(minYear)) ):
        maxYear = input("I'm sorry, but "+maxYear+ " is not a valid entry.  Please enter a positive integer value that is larger than the minimum year")

    preferencesDictionary['Minimum Year'] = minYear
    preferencesDictionary['Maximum Year'] = maxYear

    return(preferencesDictionary)

def preferencesFileBackupWriter(nameOfPreferencesFile):

    with open(nameOfPreferencesFile, 'w') as f:
        csvWriter = csv.writer(f, delimiter=',')

        backupDictionary = {
        'Minimum Mileage':0,
        'Maximum Mileage':200000,
        'Minimum Price':250,
        'Maximum Price':55000,
        'Minimum Year':1995,
        'Maximum Year':2020,
        'Scroll Down Length':150
        }
        for key in backupDictionary:
            csvWriter.writerow([key, backupDictionary[key]])


def preferencesAskAndWrite(nameOfPreferencesFile = "Preferences.csv", haveWeRunThisFunctionAtLeastOneTime = False, preferencesDictionary = {}):

    try:
        with open(nameOfPreferencesFile) as f:
            csvReader = csv.reader(f, delimiter=',')#preferences safety check
    except:
        preferencesFileBackupWriter(nameOfPreferencesFile)

    if(not haveWeRunThisFunctionAtLeastOneTime):
        changePreferencesBoolean = input('Would you like to change your preferences before starting the pogram?  Enter Y for yes, N for no, \nV to view the current preferences, or ? for information on what the preferences are. I am not case sensititve: ')
        haveWeRunThisFunctionAtLeastOneTime = True
    else:
        changePreferencesBoolean = input('Would you like to change any preferences before starting the pogram?  Enter Y for yes,  N for no, V to view the current preferences, or ? for information on what the preferences are.  I am not case sensititve: ')

    while((not(changePreferencesBoolean.lower() == 'y')) and (not(changePreferencesBoolean.lower() == 'n')) and not(changePreferencesBoolean.lower() == 'v') and (not ( changePreferencesBoolean == '?' ) )):
        changePreferencesBoolean = input("I'm sorry, but "+changePreferencesBoolean+" is not a valid input.  Please enter Y for yes, or N for no: ")

    if(changePreferencesBoolean.lower() == 'y'):

        print('Please select from the following options of preferences to change:')
        whatPreferenceToChange = input('for mileage type m, for price type p, for year type ye, l for "scroll down length," which\nis how many times it will scroll down in facebook to load in more vehicles, and to cancel type c: ')

        while((not(whatPreferenceToChange.lower() == 'm')) and (not(whatPreferenceToChange.lower() == 'p')) and (not(whatPreferenceToChange.lower() == 'ye'))and (not(whatPreferenceToChange.lower() == 'c')) and (not( whatPreferenceToChange.lower() =='l' ))):
            whatPreferenceToChange = input("I'm sorry, but "+whatPreferenceToChange+" is not a valid entry.  Please enter m for mileage, p for price, or ye for year: ")
        whatPreferenceToChange = whatPreferenceToChange.lower()
        if(whatPreferenceToChange == 'c'):
            print("Cancelling preference change, and searching for a great deal with previously saved preferences")
            return preferencesReader(nameOfPreferencesFile)
        elif(whatPreferenceToChange == 'm'):
            preferencesDictionary = mileageChange(nameOfPreferencesFile)

        elif(whatPreferenceToChange == 'p'):
            preferencesDictionary = priceChange(nameOfPreferencesFile)
        elif(whatPreferenceToChange == 'ye'):
            preferencesDictionary = yearChange(nameOfPreferencesFile)
        elif(whatPreferenceToChange == 'l'):
            preferencesDictionary = lengthChange(nameOfPreferencesFile)
        else:
            print("There has been a wierd as heck error, and if you were trying to change preferences I'm sorry but that just isn't going to happen anymore, buddy.")
            return preferencesReader(nameOfPreferencesFile)


        with open(nameOfPreferencesFile, 'w') as f:
            csvWriter = csv.writer(f, delimiter=',')

            for key in preferencesDictionary:
                    csvWriter.writerow([key,preferencesDictionary[key]])#test comment

        dictatePreferences(nameOfPreferencesFile)
        preferencesAskAndWrite(nameOfPreferencesFile, True, preferencesDictionary)

    elif(changePreferencesBoolean.lower() == 'v'):
        dictatePreferences(nameOfPreferencesFile)
        preferencesAskAndWrite(nameOfPreferencesFile, True, preferencesDictionary)
    elif(changePreferencesBoolean == '?'):
        print("\nThe preferences that can be changed are as follows:\nMinimum and maximum mileage.  You can set a range of mileages that are acceptable for you, and the scraper will only search for cars within that mileage range.")
        print("\nMinimum and maximum prices.  You can set a range of prices that are acceptable for you, and the scraper will only search for cars within that price range")
        print("\nMinimum and maximum year.  You can set a range of years that are acceptable for you, and the scraper will only search for cars within that year range")
        print("\nLength:  'length' is the number of times that the scraper will scroll to the bottom of the facebook website.  The more times it does this, the more\ncars will be searched, and the longer it will take the program to run.\n")
        preferencesAskAndWrite(nameOfPreferencesFile, True, preferencesDictionary)
    preferencesDictionary = preferencesReader(nameOfPreferencesFile)
    return preferencesDictionary











def linkGrabber(htmlSegment):
    splitSegment = htmlSegment.split('"')
    return("https://www.facebook.com"+splitSegment[3])

# The facebook Scraper is the part of the AI that goes automatically to facebook and grabs all of the car's and their information and stores it all in a list of lists
# After this, the information will be sent to the edmundsCompare function
def facebookScraper(url = 'fakeurl', scrollDownLength = 25):


    if(url == "fakeurl"):
        print("The program closed as a result of the fact that the url provided to visit facebook was invalid or missing.")
    else:
        # models = []                             #This is a list of lower case strings of models that are velid like "ferrari"
        # modelBuffer = get_makes_and_models()   outdated
        # for value in modelBuffer.values():
        #     for model in value:
        #         models.append(model.lower())

        candidates = []
        containerSplit = []
        tempLinkHolder = []
        package = []                        #List of data about car deal with following layout: ['Price', 'Year', 'Make', 'Model', - some amount of other descriptive stuff - 'number mile written in format 100k', 'the word 'miles'']
        carDict = {}
        familiarityChecker = {}

        PATH = "C:\\Users\\vesper\\Desktop\\Projects\\Python\\Facebook Market Car Scraper\\WebDriver\\chromedriver.exe"
        driver = webdriver.Chrome(ChromeDriverManager().install())

        driver.get(url)
        time.sleep(5)

        for i in range(int(scrollDownLength)):#  just heckin load this stuff up with a billion webpages
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            time.sleep(1)


        # containers = driver.find_elements_by_css_selector("div[class='b3onmgus ph5uu5jm g5gj957u buofh1pr cbu4d94t rj1gh0hx j83agx80 rq0escxv fnqts5cd fo9g3nie n1dktuyu e5nlhep0 ecm0bbzt']")

        containers = driver.find_elements_by_css_selector("div[class='kbiprv82']")#This is found in the div class just above the a class that has the url to the item,
        # which can be found by inspecting elements and checking the container that has the year make model and all of that.
          # The a class should be super long and have the url in it, and then the class right above it is the one you want.  This might change from time to time

        for container in containers:
            tempLinkHolder.append(linkGrabber(container.get_attribute("innerHTML")))

        # for container in containers:
        #     print(container.get_attribute("href")," - link tho?")
        # links = driver.find_elements_by_css_selector("div[class='kbiprv82']")
        # for link in links:
        #     print(link.text, " link?")
        # print(' - container length: ', len(containers), ". Link length: ", len(links))
        for container in containers:
            candidates.append(container.text)                   #all of this from here to VVV


        # driver.close()
        i = 0

        for containerText in candidates:
            containerSplit.append(containerText.split())
        for dataPlural in containerSplit:                           #here ^^^ are just to get down to the indviidual description words to check for car models
            i +=1
            j = 0
            recognized = False
            # print(dataPlural, i)
            # for dataSingular in dataPlural:
            #     # print(dataSingular)
            #     j+=1
            #     if(j>2):#           i>2 because the first 2 are always price and year which can only serve to heck thigns up
            #         if(dataSingular.lower() in models):
            #             print("T ")
            #             recognized = True
            #         else:
            #             print('F ')
            # if(recognized):#This part used to check against a list of car models to see if the text gathered contained a car model, but this was innefective as heck first of all,
            # and second of all checking against edmunds's URL custom was much more efficient, and effective
            package.append(dataPlural)
            package[len(package)-1].append(tempLinkHolder[i-1])

        # print('\n\n\n ---------- \n\n\n')
        i = 0
        # for car in package:
        #     # car.append(tempLinkHolder[i])
        #     i+=1
        # for thing in package:
        #     i+=1
        #     print(thing , i)
    driver.close()
    i = 0

    return package





# def kBBScraper(package, url1, url2):
#     PATH = "C:\\Users\\vesper\\Desktop\\Projects\\Python\\Facebook Market Car Scraper\\WebDriver\\geckodriver.exe"
#     driver = webdriver.Firefox()
#     url = url1+str(1)+url2
#     driver.get(url)
#     time.sleep(5)

# in the edmundsCompare function, the AI will automatically grab the "fair price" range from the website, and append it to the end of the list, if the car is a valid entry
# Before it can do this, it will attempt to access the website using the predictable URL format that edmunds.com uses, and will use this to automatically determine what is
# a valid car entry, and what is not.  Those that are invalid will be added to the "badCarPackage" variable, and later removed from the "package" variable, which is where
# all of the car information is being stored

def edmundsCompare(package, url1 = "fakeurl", url2 = "fakeurl"):

    errorCount = 0
    testInt = 0
    pricePackage = []
    badCarPackage = []
    if(url1 == "fakeurl" or url2 == "fakeurl"):
        print("The program closed as a result of the fact that the url provided to visit edmunds.com was invalid or missing.")
    else:
        PATH = "C:\\Users\\vesper\\Desktop\\Projects\\Python\\Facebook Market Car Scraper\\WebDriver\\chromedriver.exe"
        driver = webdriver.Chrome(ChromeDriverManager().install())
        print("Now retrieving pricing information from the following URLs.  There will be several errors during this phase.  This is normal, and should not be cause for concern.")
        for car in package:# package order is: price, year, make, model, detail 1... detail n, city, state, milage, the word "miles"
# this is giong to be the majority of the work preformed in this function.  It is giong to go through every car in the "package" of cars that was recieved from the facebook scraper, and compare their price to the prices shown on edmunds.com, and append a price ratio value to that car's entry in the package, then re return the package again for analyisis
            url = url1+car[2]+"/"+car[3]+"/"+car[1]+"/"+url2
            print(url)
            try:
                # soup = BeautifulSoup(, 'lxml')
                # driver = webdriver.Chrome(PATH)
                driver.get(url)
                # time.sleep(1)

                # tableContainer = soup.find('div', class_='estimated-values estimated-values-visible')#Beautifulsoup method (headless)
                tableContainer = driver.find_elements_by_css_selector("div[class='estimated-values estimated-values-visible']")#webdriver method
                for thing in tableContainer:
                    # table = tableContainer.
                    table = thing.find_elements_by_css_selector('table[class="estimated-values-table text-gray-darker mb-0_5 mt-1_5 table"]')
                for somestuff in table:
                    cells = somestuff.find_elements_by_css_selector('td[class="text-right"]')
                pricesTemp = []
                prices = []
                for cell in cells:
                    pricesTemp.append(cell.get_attribute('innerHTML'))
                for price in pricesTemp:
                    try:
                        value = Decimal(sub(r'[^\d.]', '', price))
                        prices.append(value)
                    except:
                        prices.append(Decimal(999999))
                # pricePackage.append(prices)
                car.insert(1, prices)
                # The prices will be ordered left to right, up to down from a table with the columns of trade in, private party, dealer retail, and the rows of: outstanding, clean, average, and rough
                # such that the first three are from outstanding, and are ordered in order of trade in, private party, and dealer retail, and so on
                # for price in prices:
                #     print(price, " - price?")
                # time.sleep(5400)
                # driver.close()
                    # time.sleep(2)
            except:
                errorCount +=1
                print("Error attempting to access url: "+url1+car[2]+"/"+car[3]+"/"+car[1]+"/"+url2+". ", errorCount)
                badCarPackage.append(car)
                time.sleep(1)
                # driver.close()
        for car in badCarPackage:
            package.remove(car)
        driver.close()
        return([package, pricePackage])

            # print(tableContainer, " - table")

            # theThingWeNeedQuestionMark = table.get_attribute('innerHTML')
            # print(theThingWeNeedQuestionMark)

            # print(table.find_elements_by_css_selector("td[class='text-right']" + " This is the thing in the table"))

# The priceCompacter makes the data from edmunds more usable, as it is given in a range, it averages some of the numbers together so that it is more easy to use

def priceCompacter(carPackage):
    i = 0
    j = 0
    accumulator = 0
    tempCompactedPricePackage = []
    compactedPricePackage = []
    badCarPackage = []
    for car in carPackage:
        # print(car, " okay here is the car, ", car[1])
        try:
            # print("checkpoint 1")
            for price in car[1]:#for price in the array of prices grabbed from edmunds
                # print("checkpoint 2")
                accumulator += price
                i += 1
                if(i > 2):
                    # print("checkpoint 3")
                    accumulator /= 3
                    tempCompactedPricePackage.append(accumulator)
                    i = 0
                    accumulator = 0
            # print("checkpoint 4")
            car.insert(2, tempCompactedPricePackage)
            tempCompactedPricePackage = []
        except:
            print("Unworkable car that will be removed automatically: ", car)
            badCarPackage.append(car)

    for car in badCarPackage:
        carPackage.remove(car)
    return(carPackage)

# The price comparer function uses the mileage as a barometer for how good of condition the car is in, and uses this to choose a price from the price range that edmunds delivered
# If the mileage is lower, it uses the better condition's pricing, and if the mileage is worse it uses the worse condition's pricing

def priceComparer(carPackage, pricePackage):

    offsetForMileage = 3
    compactedPricePackageIndex = 2
    priceAveragePackage = []
    priceRatioPackage = []
    average = 0
    badCarBoyVeryBadAndNaughty = []
    ratio = 0
    # for priceList in pricePackage:
    #     average = 0
    #     for price in priceList:
    #         average += price
    #     average /= len(priceList)
    #     priceAveragePackage.append(average)

    # i = 0
    # for price in priceAveragePackage:
    #     ratio = priceAveragePackage[i]/carPackage[i][0]
    #     carPackage[i].insert(0, ratio)
    #     i +=1

    i = 0
    for car in carPackage:
        try:

            if(int(car[len(car)-offsetForMileage]) <40000):#Depending on the mileage, use the price of Great, good, okay, or bad.  also insert a tier list ranking in case we must check later
                ratio = car[compactedPricePackageIndex][0]/car[0]
                car.insert(0, 's')

                car.insert(0, ratio)
            elif(int(car[len(car)-offsetForMileage]) <70000):
                ratio = car[compactedPricePackageIndex][1]/car[0]
                car.insert(0, 'a')

                car.insert(0, ratio)
            elif(int(car[len(car)-offsetForMileage]) <100000):
                ratio = car[compactedPricePackageIndex][2]/car[0]
                car.insert(0, 'b')

                car.insert(0, ratio)
            else:
                ratio = car[compactedPricePackageIndex][3]/car[0]
                car.insert(0, 'c')

                car.insert(0, ratio)
            i+=1

        except:

            badCarBoyVeryBadAndNaughty.append(car)
            # carPackage.remove(car)


    # tempArrayForStuffProgrammingPractice = []
    # for car in carPackage:
    #     tempArrayForStuffProgrammingPractice.append(car[0])
    i = 1
    for car in badCarBoyVeryBadAndNaughty:
        print("Unworkable car that will be removed automatically: ",car," ",i)
        carPackage.remove(car)
        i +=1
    ratioSpot = lambda car: float(car[0])
    carPackage.sort(key=ratioSpot, reverse=True)
    return(carPackage)

# This function cleans the data for the mileage.  Some cars do not have mileages, and any of the facebook entries which do not work with this function are automatically remoevd
def mileDataCleaner(carPackage):
    offsetForMileage = 3
    i = 0
    badCarPackage = []
    for car in carPackage:
        try:
            mileString = car[len(car)-offsetForMileage]
            tempString = mileString.rstrip('K')
            tempString = tempString+"000"
            carPackage[i][len(car)-offsetForMileage] = tempString
            i +=1
        except:
            badCarPackage.append(car)
        for car in badCarPackage:
            carPackage.remove(car)
    return(carPackage)





def preferencesRead():
    try:
        with open("Preferences.txt") as f:
            text = f.read()
    except FileNotFoundError:
        text = None
        print("Error attempting to read preferences file. It appears to be missing... Please...  PLEASE GOD GIVE ME BACK MY PREFERENCES FILE!")
    return(text)

def fakePriceBumper(carPackage):#this is just to get rid of the fake prices like 1234 and what not.

    i = 0
    for car in carPackage:
        if("1234" in str(car[0])):
            i+=1
            carPackage.remove(car)
            print(car," This car had the price '1234..', and as such has been automatically removed to increase efficiency ",i)
    return carPackage

# ------------------------------------------------------------------------------ S T A R T---------------------------------------------------------------------------------------------------------------------------------
# start -- start -- start -- start -- start -- start -- start -- start -- start -- start -- start -- start -- start -- start -- start -- start -- start -- start -- start -- start -- start -- start -- start -- start --
# ------------------------------------------------------------------------------ S T A R T---------------------------------------------------------------------------------------------------------------------------------
nameOfPreferencesFile = "Preferences.csv"
preferencesDictionary = preferencesAskAndWrite(nameOfPreferencesFile)
facebookMarketUrl = 'https://www.facebook.com/marketplace/atlanta/vehicles?'
scrollDownLength = 25

try:
    scrollDownLength = preferencesDictionary['Scroll Down Length']
except:
    pass

try:
    facebookMarketUrl1 = 'https://www.facebook.com/marketplace/atlanta/vehicles?'
    facebookMarketUrl2 = 'minPrice='+str(preferencesDictionary['Minimum Price'])+'&'
    facebookMarketUrl3 = 'maxPrice='+str(preferencesDictionary['Maximum Price'])+'&'
    facebookMarketUrl4 = 'maxMileage='+str(preferencesDictionary['Maximum Mileage'])+'&'
    facebookMarketUrl5 = 'maxYear='+str(preferencesDictionary['Maximum Year'])+'&'
    facebookMarketUrl6 = 'minMileage='+str(preferencesDictionary['Minimum Mileage'])+'&'
    facebookMarketUrl7 = 'minYear='+str(preferencesDictionary['Minimum Mileage'])+'&exact=false'

    facebookMarketUrl = facebookMarketUrl1+facebookMarketUrl2+facebookMarketUrl3+facebookMarketUrl4+facebookMarketUrl5+facebookMarketUrl6+facebookMarketUrl7

except:
    print("There was an error retrieving the preferences.  The program will continue without any preferences at all by default")

# kBBUrl1 = "https://www.kbb.com/kia/seltos/2021/35-sedan-4d/?vehicleid="
# kBBUrl2 = "&intent=buy-new&category=suv"
edmundsUrl1 = "https://www.edmunds.com/"
edmundsUrl2 = "appraisal-value/#expressPath"

carPackage = facebookScraper(facebookMarketUrl, scrollDownLength)
# carPackage = [["$2,300", "2003", "Nissan", "Maxima", "Silver", "Atlanta", "Georgia", "50k", "miles"], ["$2,300", "2003", "Nissan", "Altima", "Silver", "Atlanta", "Georgia", "120k", "miles"]] #test package
#test package
for car in carPackage:
    try:
        car[0] = Decimal(sub(r'[^\d.]', '', car[0]))#this turns the first value (the price) of the car from a string into a decimal
    except:
        carPackage.remove(car)
packagePackage = edmundsCompare(carPackage, edmundsUrl1, edmundsUrl2)

carPackage = packagePackage[0]
pricePackage = packagePackage[1]

carPackage = mileDataCleaner(carPackage)
carPackage = priceCompacter(carPackage)


carPackage = fakePriceBumper(carPackage)

finalCarPackage = priceComparer(carPackage, pricePackage)#This adds the ratio data to the beginning of the car package






now = datetime.now()
currentDateTime = now.strftime("%d-%m-%Y %H-%M-%S")
outputName = 'Facebook Market Scraper Output-'+currentDateTime+'.xlsx'

with open(outputName, 'w') as outputFile:
    header = ['Ratio', 'Price', 'Mileage', 'Make', 'Model', 'Year', 'Edmunds URL', 'Facebook URL' ]

    csvWriter = csv.writer(outputFile, delimiter='\t')

    csvWriter.writerow(header)

    for car in finalCarPackage:
        edmundsUrl = edmundsUrl1+car[6]+'/'+car[7]+'/'+car[5]+'/'+edmundsUrl2
        csvWriter.writerow([str(round(car[0], 3)), str(car[2]), str(car[len(car)-3]),str(car[6]), str(car[7]), str(car[5]), edmundsUrl, car[len(car)-1]])

print("The program is now completed, and the output can be located in the file named: ",outputName)
print("I will close automatically after 5 minutes")
time.sleep(300)
