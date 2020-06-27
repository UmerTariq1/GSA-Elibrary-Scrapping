import requests
from bs4 import BeautifulSoup 
from pathlib import Path
import os
import sys
import time
import re
import traceback
import json
from string import ascii_uppercase



downloadPath = "C:\\Users\\Administrator\\Desktop\\UmerCode\\download\\"  #slashes at the end are necessary
DB_URL = 'http://blackvoltrontechs.com/transviti/GSA_scrap'
startLetter = 'A'     # starting alphabet (in the base link) is 'A'
startFrom = 0         # starting link number in a page


basicLink1="https://www.gsaelibrary.gsa.gov/ElibMain/"
basicLink2 = "contractorList.do?contractorListFor="   #seperate because basicLink1 is used by sub urls too.
bad_chars = "\\/:?*\"<>|"
bad_chars_list = ["\\","/",":","?","*","\"","<",">","|"]


def RemoveUnwwantedCharacters(myStr):
    myStr2 = ""
    for letter in myStr:
        if letter not in bad_chars_list:
            myStr2 += letter
    return myStr2

def GetLink(link):
    try:
        time.sleep(1)
        request=requests.get(link)
    except requests.exceptions.ConnectionError:
        print("Connection refused")
        print("Sleeping for 5 seconds")
        time.sleep(5)
        try:
            request=requests.get(link)
        except requests.exceptions.ConnectionError:
            print("Connection refused 2nd time.")
            print("Sleeping for 15 seconds")
            time.sleep(15)
            try:
                request=requests.get(link)
            except requests.exceptions.ConnectionError:
                print("Connection refused 3rd time.")
                print("Sleeping for 30 seconds")
                print("Link that is causing issue : " + str(link))
                time.sleep(30)
                try:
                    request=requests.get(link)
                except requests.exceptions.ConnectionError:
                    print("Connection refused 4th and last time. Will exit now")
                    print("Sleeping for 60 seconds")
                    time.sleep(60)
                    try:
                        request=requests.get(link)
                    except requests.exceptions.ConnectionError:
                        print("Connection refused 4th and last time. Will exit now")
                        print("Sleeping for 5 minutes")
                        time.sleep(300)
                        request=requests.get(link)


    return request


def downloadFile(url, fileName):
    with open(fileName, "wb") as file:
        response = requests.get(url)
        file.write(response.content)

# link = outer link, list wala page hai ye
# subLink = list k har item ka page ka link
# linkCounter 
# FileHtmURL
# linkText

def UpdateDictionaryList(dictList,dict_var):
    dictList.append(dict_var)                    # append doesnt return anything so it will just  append to refrenced list

#make dictionary is called from 2 places. from handle special cases function and from the part where everything is good and file exist and so called just before downloading file 
def makeDictionary(link,linkText,linkCounter,subLink,isFileExist, FileHtmURL, contractorInformationHTML,caseName="Everything Okay.",caseText="Everything Okay"):        
    dataDictionary = {}
    dataDictionary["BaseLink"] = str(link)
    dataDictionary["BaseLinkText"] = str(linkText)
    dataDictionary["LinkNumberInBaseLink"] = str(linkCounter)
    dataDictionary["SpecificContractInformationLink"] = str(subLink)
    dataDictionary["isFileExist"] = str(isFileExist)
    dataDictionary["CaseName"] = str(caseName)
    dataDictionary["CaseText"] = str(caseText)
    dataDictionary["FileURL"] = str(FileHtmURL)
    dataDictionary["ContractorInformationTableHTML"] = str(contractorInformationHTML)

    #print(requests.post(DB_URL, params=dataDictionary))
    return dataDictionary
    

def makeFolderIfNotExist(pageLetter,lastFolderName):
    global downloadPath

    Path(downloadPath+pageLetter+"\\"+lastFolderName).mkdir(parents=True, exist_ok=True,mode=0o777)


def write_record(filePath,record):
    with open(filePath, 'w') as file:
        file.write(json.dumps(record,indent=2)) # use `json.loads` to do the reverse

def append_record(filePath,record):
    with open(filePath, 'a') as f:
        f.write(json.dumps(record, indent=2))
        
def read_record(filePath):
    with open(filePath) as f:
        my_list = [json.loads(line) for line in f]
    return my_list

def HandleSpecialLinkCases(caseName, caseText, link,linkText,linkCounter,subLink, pageLetter, folderName,isFileExist=False, FileHtmURL="", contractorInformationHTML="",fileNumber=0 ):
    print("\n-----------------------------------------------------------------------------------------")
    print(caseText)
    print("linkCounter : ",linkCounter)
    print("-----------------------------------------------------------------------------------------")

    
    dataDictionary = makeDictionary(link,linkText,linkCounter,subLink,isFileExist, FileHtmURL, contractorInformationHTML,caseName,caseText)
    
    if caseName == "GsaError":
        FileHtmURL ="http://www.gsa.gov/s2"
    elif caseName == "NoRedirection":
        FileHtmURL = "No file/table avaiable."
    else:
        FileHtmURL = "No file/table avaiable"
        
    makeFolderIfNotExist(pageLetter,folderName)
    destinationPath = (downloadPath+pageLetter+"\\"+folderName+"\\"+"content_" + str(fileNumber) + ".json")
    write_record(destinationPath,dataDictionary)



def StartScrapping_internal(pageLetter,soup,link):
    global downloadPath
    global DB_URL
    global startLetter
    global startLetter
    global startFrom 
    global basicLink1
    global basicLink2
    global bad_chars
    global bad_chars_list    
    
    
    totalTime = 0
    avgTime = 0

    rows = soup.find("table", border=1).find_all("tr")    # get all rows

    linkCounter = 0
    processedLinkCounter = 0
    try:
        print("Total Number of rows : " + str(len(rows)))
        for row in rows:             # traverse over all rows

            columns = row.find_all("td")
            for columnIndex,column in enumerate(columns):        

                linkCounter+=1
                print(linkCounter,end=", ")
                
                if linkCounter<startFrom:     #set this value to the number of links already processed. set 0 if none. used in case error appeared and now want to resume instead of restart completely.
                    continue
                
                startFrom = 0       #resetting it so next alphabet doesnt start from the given number. as the purpose was to start only that specific alphabet with that link number/counter    
                processedLinkCounter+=1
                startTime = time.time()

                isFileExist = False
                FileHtmURL =""

                linkText = column.get_text()     # get the text of the link i.e name of the contractor

                folderName = RemoveUnwwantedCharacters (linkText)   # setting folder name as the contractor name minus not allowed characters (bad characters: definde above)
                subURL = row.find_all("td")[columnIndex].find('a',href=True)['href']

                subLink=basicLink1 + subURL        
                subRequest = GetLink(subLink)

                subSoup=BeautifulSoup(subRequest.text,'html.parser')
                try:
                    contractorInformationHTML = subSoup.find_all("table")[10]
                    FileTable = subSoup.find_all("table")[8].find_all("table")[7].find_all("tr")[1].find_all("td")[3].find_all("a")
                except:   #if there is no File table in contractor information
                    caseText = "There is no table in sub link."
                    caseName = "file_Table"               
                    contractorInformationHTML = "" 
                    isFileExist = False
                    HandleSpecialLinkCases(caseName, caseText, link,linkText,linkCounter,subLink, pageLetter, folderName,isFileExist, FileHtmURL,
                                            contractorInformationHTML )
                    continue
                
                if len(FileTable) == 0:    #if there is no File in contractor information
                    caseText = "There is no file in the table"
                    caseName = "file_Table"
                    isFileExist = False
                    HandleSpecialLinkCases(caseName, caseText, link,linkText,linkCounter,subLink, pageLetter, folderName,isFileExist, FileHtmURL,
                                                contractorInformationHTML  )
                
                else:                      # if there is  atleast one file
                    fileNumber = 0                                  # File number in the table. used in placing content.json. content.json will now look like content_1.json for first file and content_2.json        
                    for fileTablePart in FileTable:                    # there can be multiple files in one link so traverse over all of them
                        fileNumber = fileNumber + 1
            
                        FileHtmURL = fileTablePart["href"]
                        fileUrlShort = FileHtmURL.rsplit("/",1)[0]+"/"
                        
                        if (FileHtmURL == "http://www.gsa.gov/s2"):    # some file links are gsa.gov instead of htm links (htm links redirects to either pdf or docx file)
                            caseText = "File link is = http://www.gsa.gov/s2"
                            caseName = "GsaError"
                            isFileExist = False
                            HandleSpecialLinkCases(caseName,caseText, link,linkText,linkCounter,subLink, pageLetter, folderName,isFileExist, FileHtmURL, contractorInformationHTML )
                            
                        else:      # file exists and has htm url and that means it will have a file. need to go to htm url and meta tag for actual file url
                            # For downloading files
                            FileHtmRequest = GetLink(FileHtmURL)   #going to htm url , it redirects to file 
                            FileHtmSoup =BeautifulSoup(FileHtmRequest.text,'html.parser')      
                            fileHtmResultException = False              
                            try:                        # some files have links but links are broken so this will deal with it
                                FileHtmResult = FileHtmSoup.find("meta")["content"]                 # file url is in meta of htm file     

                                if "url=" not in str(FileHtmResult):   # some links have file but their htm tags have text and do not redirect somewhere
                                    caseText = "No redirects found. Its direct text."
                                    caseName = "NoRedirection"
                                    isFileExist = False
                                    HandleSpecialLinkCases(caseName,caseText, link,linkText,linkCounter,subLink, pageLetter, folderName,isFileExist, FileHtmURL, contractorInformationHTML )

                                else:
                                    FilemetaURL = FileHtmSoup.find("meta")["content"].split("url=")[1] #get the file url from middle url that redirects
                                    redirectedFileURL = fileUrlShort+FilemetaURL            # arranging the file url.
                                    extension = redirectedFileURL.split(".")[-1].lower()    # files are usually pdf or docx but code can handle any format
                                    fileName = FileHtmURL.rsplit("/",2)[1] + "." +extension    # get the file name seperately and add extension to it. file name is at the end of  htm url
                                    fileName = RemoveUnwwantedCharacters(fileName)      # path shouldnt contain bad characters. bad characters are define at the top

                                    isFileExist = True
                                    dataDictionary = makeDictionary(link,linkText,linkCounter,subLink,isFileExist, FileHtmURL, contractorInformationHTML)
                                    makeFolderIfNotExist(pageLetter,folderName)
                                    destinationPath = (downloadPath+pageLetter+"\\"+folderName+"\\"+"content_" + str(fileNumber) + ".json")

                                    # For logging in filesystem
                                    write_record(destinationPath,dataDictionary)

                                    destinationPath = (downloadPath+pageLetter+"\\"+folderName+"\\"+fileName)   # path for download file
                                    downloadFile(redirectedFileURL, destinationPath)
                                
                            except Exception as e:                                          # for 404 error handling.
                                caseText = "File link is broken"
                                caseName = "file_Table"
                                isFileExist = False
                                HandleSpecialLinkCases(caseName, caseText, link,linkText,linkCounter,subLink, pageLetter, folderName,isFileExist, FileHtmURL,contractorInformationHTML  )
                            
                endTime = time.time()
                totalTime = totalTime + (endTime-startTime)
                avgTime = totalTime/processedLinkCounter

                if linkCounter%10==0:                               #General logging after processing 10 links
                    print("\n\n Total links  = "+ str(linkCounter))
                    print("Total links processed = "+ str(processedLinkCounter))
                    print("Total elapsed time (in seconds) = "+str(totalTime))
                    print("Average link time (in seconds)  = "+ str(avgTime))
                    print("\n")
        return 0              
    except Exception as e:
        errorLogDictionary = {}
        errorLogDictionary["linkCounter"] = str(linkCounter)
        errorLogDictionary["pageLetter"] = str(pageLetter)
        errorLogDictionary["link"] = str(link)
        errorLogDictionary["linkText"] = str(linkText)
        errorLogDictionary["subLink"] = str(subLink)
        errorLogDictionary["Error"] = str(e)
        errorLogDictionary["Traceback"] = str(traceback.format_exc())
        destPath = downloadPath+"Error.json"
        write_record(destPath,errorLogDictionary)

        print("\n\n General error occured. ")
        print("last instances of below items are : ")
        print("linkCounter = " + str(linkCounter))
        print("pageLetter = " + str(pageLetter))
        print("link = " + str(link))
        print("linkText = " + str(linkText))
        print("subLink = " + str(subLink))
        print("Error : ")
        print(e)
        print("Traceback: ")
        print(traceback.format_exc())


        return 1
        
        


def StartScrapping():
    global startLetter
    global basicLink1
    global basicLink2

    shouldPass = True       # jb tk true hai tu scrap nahi karna. jis letter pe karna hai wo isko false karde ga

    for pageLetter in ascii_uppercase:
        # get the basic list page of  letter

        if pageLetter == startLetter:
            shouldPass = False
        if not shouldPass:

            print("Starting for Page= "+ pageLetter)
            link=basicLink1 + basicLink2 + pageLetter
            print("link= "+link)
            r = GetLink(link)    
            soup=BeautifulSoup(r.text,'html.parser')
            resp = StartScrapping_internal(pageLetter,soup,link)
            if resp==1:
                return 1

def CountRowsForEachAlphabet():
    totalRows= 0
    totalLinks = 0
    for pageLetter in ascii_uppercase:
        print("Starting for Page= "+ pageLetter, end="   ")
        link=basicLink1 + basicLink2 + pageLetter
        r = GetLink(link)    
        soup=BeautifulSoup(r.text,'html.parser')
        rows = soup.find("table", border=1).find_all("tr")    # get all rows
        print("Total Number of rows in this alphabet link: " + str(len(rows)))       
        totalRows = totalRows + len(rows)     
        totalLinks = totalLinks + (len(rows)*3)
        print("Each row has 3 links mostly. so total links for the alphabet are around =  3*rows => ", (len(rows)*3))
        print("----------------------------------")

    print("----------------------------------")
    print("Summary :")
    print("Total Rows => ", totalRows )
    print("Total number of links in the whole contractor site are around => ",totalLinks)

if __name__ == '__main__':
    #for normal scrapping
    if StartScrapping() == 1:
        print("Unfinished. Error Occured.")
    else:
        print("Finished. Success")

    #if you want to count rows in each alphabet link:
    # CountRowsForEachAlphabet()



