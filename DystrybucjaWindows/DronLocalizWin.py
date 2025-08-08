import glob
import click
import os
from geopy.geocoders import Nominatim
import re
from time import sleep
import linecache
import shutil
import sys

detailedhelptext = f"OPIS\n\nDronLocalizer jest przede wszystkim konwerterem położeń geograficznych drona DJI zapisanych w pliku .SRT na jego aktualny adres. Oprócz tego umożliwia prostą edycję napisów.\nPliki SRT w kontekście dronów DJI to pliki tekstowe, zawierające informacje takie jak czas i treść napisów, parametry kamery itp. Pliki SRT są generowane automatycznie podczas nagrywania jeśli funkcja napisów jest włączona w ustawieniach aplikacji DJI Go. Dodatkowo format video należy ustawić na MP4 i włączyć funkcję napisów (Video Caption).Pliki MP4 i SRT są zapisywane podczas nagrywania na karcie SD.\n\nUŻYCIE\n\n1) Na laptopie z systemem Windows 10/11 utworzyć dowolny katalog o nazwie np. C:\\Users\\TwojaNazwa\\DJI_Video.\n2) Pliki MP4 i SRT skopiować z karty SD do katalogu DJI_Video.\n3) Do katalogu tego przekopiować również wszystkie pliki programu {os.path.basename(__file__).strip('.py')}.\n4) Otworzyć wiersz polecenia (terminal): w W11 Naciśnij klawisz Windows i klawisz R (Win + R) lub np. kliknąć prawym przyciskiem myszy na menu Start i wybrać \"Terminal\" (lub \"Wiersz polecenia\").\n5)W terminalu zmień właściwy katalog. Użyj w tym celu polecenia cd aby przejść do katalogu ze skopiowanymi tam plikami programu MP4 i SRT, czyli wpisz cd, a następnie ścieżkę do tego katalogu, np. cd C:\\Users\\TwojaNazwa\\DJI_Video\n6) Uruchom program wpisując {os.path.basename(__file__).strip('.py')}.exe -r True\n7) Wybierz odpowiedni plik SRT (w katalogu możesz mieć ich więcej) i podaj odpowiedzi na kolejne pytania dotyczące wielkości i kolorów trzcionek, a także lokalizacji napisów na ekranie. Naciskając ENTER w pustym polu wyboru możesz się dowiedzieć jakie wartości ono może przyjmować.\n8) W kolejnych polach możesz podać dodatkowy napis opisujący np. sfilmowane zdarzenie, oraz parametry jego trzcionki. Pole można pozostawić puste.\n9) Ostatnią wielkością którą trzeba podać jest dokładność zaokrąglenia współrzędnych geograficznych, czyli ilość cyfr po przecinku. Wartość ta jest o tyle istotna, że wpływa na dokładność określenia adresu i czas wykonywania konwersji. Im cyfra ta jest większa, tym dokładność określenia adresów jest również większa, ale częstotliwość zapytań internetowych także rośnie. Może to niekiedy powodować przeciążenie serwerów internetowych, które to wtedy zrywają połączenie. W przypadku takim należy uruchomić program w innych godzinach lub zmniejszyć dokładność.\n\nUWAGI KOŃCOWE\n\n-Ze wspomianych już względów wymagany jest dostęp do internetu.\n-W nawiasach kwadratowych podane są wartośći domyślne, akceptowane przez ENTER.\n-Operacja konwersji dla danego pliku SRT jest oczywiście jednorazowa\n-Program tworzy kopię oryginalnego pliku SRT. Kopia ta ma rozszerzenie .SRT_copy. Zawsze można do niej wrócić."

@click.command()
@click.option('-r', help='Gdy zamiast TEXT wpiszemy True spowoduje to uruchomienie programu')
@click.option('-h', help='Gdy zamiast TEXT wpiszemy True spowoduje to wyświetlenie opisu programu')

def main(r, h):
    
    if r==None and h==None:
        print(f"Spróbuj: {sys.argv[0]} --help")
    if h:
        print(detailedhelptext) 
    if r:   
        SRTfiles = []
        i = 0
        for file in glob.glob("*_D.SRT"):  # create array of *_D.SRT files
            print(f"{i}) {file}")
            i+=1
            SRTfiles.append(file)

        if len(SRTfiles) == 0:
            sys.exit('nie ma plików ..._D.SRT')

        #{\\an7} subtitles at top-left, {\\an8} at top-centre, {\\an9} at top-right, {\\an4} at middle-left, {\\an5} at middle-center,
        #{\\an6} at middle-right, {\\an1} at bottom-left, {\\an2} at bottom-centre, {\\an3} at bottom-right
        subdep_dict = {'gora-lewa':'{\\an7}', 'gora-srodek':'{\\an8}', 'gora-prawa':'{\\an9}', 'srodek-lewa':'{\\an4}', 'srodek-srodek':'{\\an5}',    'srodek-prawa':'{\\an6}', 'dol-lewa':'{\\an1}', 'dol-srodek':'{\\an2}', 'dol-prawa':'{\\an3}'} 

        class InputFileParamType(click.ParamType):  # to select SRT file 
            name = "SRT file name"

            def convert(self, user_input, param, ctx):
                try: 
                    file_number = int(user_input)
                except ValueError: 
                    self.fail(f"{user_input} numer wyboru musi być liczbą całkowitą!", param, ctx) 
                if file_number < 0 or file_number > len(SRTfiles)-1: 
                    self.fail(f" wybór musi być liczbą całkowitą z zakresu 0-{len(SRTfiles)-1}", param, ctx)
                else:
                    file_name = SRTfiles[file_number]
                    print(f' wybrano {file_name}')
                    if os.path.isfile(file_name + '_copy'):  
                        shutil.copy(file_name + '_copy', file_name)  # copy copied file to original SRT file (if exists)
                    else:
                        if os.path.isfile(file_name):
                            pattern = re.compile(r'(.+)')
                            copy_file_name= pattern.sub(r'\1_copy', file_name)
                            shutil.copy(file_name, copy_file_name)  # create a copy of the original SRT file                  
                return file_name      

        class FontSizeParamType(click.ParamType):  # to select font size 
            name = "font size"

            def convert(self, user_input, param, ctx):
                try:
                    font_size = int(user_input)
                    min_font_size = 5
                    max_font_size = 150
                except ValueError: 
                    self.fail(f"{user_input} rozmiar trzcionki musi być liczbą całkowitą!", param, ctx)
                if font_size < min_font_size or font_size > max_font_size:
                    self.fail(f" rozmiar trzcionki musi być liczbą całkowitą z zakresu {min_font_size}-{max_font_size}", param, ctx)
                else:
                    print(f' wybrano trzcionke o rozmiarze {font_size}\n')    
                return font_size
            
        color_text = " kolor może być jednym z następujących: black, white, red, blue, SkyBlue, LightBlue, green, PaleGreen, silver, gray, yellow, purple, maroon, olive, lime, aqua, teal, navy, fuchsia, salmon, DarkSalmon"   
        class FontColorParamType(click.ParamType):  # to select font color
            name = "font color"

            def convert(self, user_input, param, ctx):
                colors = ['black', 'white', 'red', 'blue', 'SkyBlue', 'LightBlue', 'green', 'PaleGreen', 'silver', 'gray', 'yellow', 'LightYellow', 'purple', 'maroon', 'olive', 'lime', 'aqua', 'teal', 'navy', 'fuchsia', 'salmon', 'DarkSalmon'] 
                
                font_color = user_input
                if font_color in colors:
                    print(f' wybrano kolor {font_color}\n')
                else:
                    self.fail(color_text, param, ctx)    
                return font_color

        deployment_text = " rozmieszczenie może być jedno z nastepujących: gora-lewa, gora-srodek, gora-prawa, srodek-lewa, srodek-srodek, srodek-prawa, dol-lewa, dol-srodek, dol-prawa"   
        class SubtitlesDeploymentParamType(click.ParamType):  # to select deployment of main subtitles
            name = "subtitles deployment"

            def convert(self, user_input, param, ctx):
                deployments =  subdep_dict
                
                sub_deployment = user_input
                if sub_deployment in deployments.keys():
                    print(f' wybrano rozmieszczenie {sub_deployment}\n')
                else:
                    self.fail(deployment_text, param, ctx)    
                return sub_deployment 
            
        class VideoNoteParamType(click.ParamType):  # any additional subtitle (note)
            name = "additional video note"

            def convert(self, user_input, param, ctx): 
                
                note = user_input
                max_note_len = 50
                if len(note) > max_note_len:
                    #print(f'dodatkowa informacja nie może być dłuższa niż {max_note_len}\n')
                    self.fail(f" dodatkowa informacja nie może być dłuższa niż {max_note_len} znaków!", param, ctx)          
                return note
            
        class VideoNoteDeploymentParamType(click.ParamType):  # to select deployment of any additional subtitle (note)
            name = "additional video note deployment"

            def convert(self, user_input, param, ctx):
                deployments =  subdep_dict
                
                note_deployment = user_input
                if sub_deployment in deployments.keys():
                    print(f' wybrano rozmieszczenie {sub_deployment}\n')
                else:
                    self.fail(deployment_text, param, ctx)    
                return note_deployment           
            
        class GeoCoordPrecisionParamType(click.ParamType):  # to set geo coordinates precision
            name = "geo coordinates precision"

            def convert(self, user_input, param, ctx):
                try:
                    coord_prec = int(user_input)
                except ValueError: 
                    self.fail(f"{user_input} Dokładność współrzędnych geograficznych to ilość cyfr po przecinku do której współrzędne zostaną zaokrąglone. Musi to być liczba całkowita!", param, ctx)
                if coord_prec < 0 or coord_prec > 6:
                    self.fail(" dokładność współrzędnych geograficznych musi być liczbą całkowitą z zakresu 0-6", param, ctx)
                else:
                    print(f' wybrano doładność {coord_prec} cyfr po przecinku')    
                return coord_prec         

        file_name = click.prompt("Wybierz numer pliku SRT", type=InputFileParamType()) 

        font_size = click.prompt("Wpisz rozmiar trzcionki", default='50', type=FontSizeParamType())
        print(color_text)
        font_color = click.prompt("Wpisz kolor trzcionki", default='white', type=FontColorParamType())
        print(deployment_text)

        sub_deployment = click.prompt("Wybierz lokalizację napisów", default='dol-srodek', type=SubtitlesDeploymentParamType())
        sub_deployment = subdep_dict[sub_deployment]

        note = click.prompt("Wpisz ewentualną informację dodatkową", default='', type=VideoNoteParamType())
        if len(note) > 0:
            note_font_size = click.prompt("Wpisz rozmiar trzcionki dla informacji dodatkowej", default='50', type=FontSizeParamType())
            note_font_color = click.prompt("Wpisz kolor trzcionki dla informacji dodatkowej", default='white', type=FontColorParamType())
            note_line = '<font size="' + str(note_font_size) + '" color="' + note_font_color + '"> ' + note + ' </font>' + '\n'
        else:
            note_line = '' 

        coord_prec = click.prompt("Wpisz dokładność zaokrąglenia współrzędnych geograficznych (ilość cyfr po przecinku)", default='4', type=GeoCoordPrecisionParamType())

        class GeoDict:  # to create addresses dictionary
            def __init__(self):
                self.dictionary = {}
                
            def set_address(self, lat, lon, address):
                    self.dictionary[(lat, lon)] = address   

            def get_address(self, lat, lon):
                if (lat, lon) in self.dictionary:
                    return self.dictionary[(lat, lon)]
                return None
            
        addresses_dict = GeoDict()  # addresses dictionary

        geolocator = Nominatim(user_agent="my-app")

        f_tmp = open("sub_out.txt", encoding='utf-8', mode="w")

        # regular expressions patterns to select the relevant parts of the lines
        pattern_frame_time_line = re.compile(r'(\d\d.+? --> .+?)\n')
        pattern_geoloc = re.compile(r'(.+?)latitude: (-{0,1})(\d+\.\d+).+longitude: (-{0,1})(\d+\.\d+)(.+?\n{0,1})$')
        pattern_rel_alt = re.compile(r'.+?rel_alt: (-{0,1})(\d+\.\d+).+?\n{0,1}$')
        pattern_datetime = re.compile(r'(\d+-\d+-\d+ .+?)\..+\n')

        pattern_line_to_remove = re.compile(r'<font.+?FrameCnt:.+?\n')  # to remove line with ....FrameCnt:....

        alt_text = 'Wysokość względna/Relative altitude: '

        shutil.copy(file_name, 'change.SRT')  # change.SRT is only temporary file in order to process SRT file
        ft = open("change.SRT", encoding='utf-8', mode="r")
        total_lines = len(ft.readlines())
        print('Total Number of lines:', total_lines)  

        i = 0  # number of line
        with open("change.SRT", encoding='utf-8') as Text:  # main loop
            for line in Text:
                i += 1
                print(str(i) + '/' + str(total_lines))
                frame_time_line = pattern_frame_time_line.findall(line)
                line_to_remove = pattern_line_to_remove.findall(line)
                actuall_geocoord = pattern_geoloc.findall(line)
                datetime = pattern_datetime.findall(line)
                if len(frame_time_line) > 0:  # line with timestamps separated by a -->
                    line =  pattern_frame_time_line.sub(r'\1', line) + '\n' + sub_deployment + '\n'   
                if len(line_to_remove) > 0:
                    line = ""    
                if len(datetime) > 0:  # if found line with date and time
                    datetime_str = pattern_datetime.sub(r'\1', line)
                    line = note_line + '<font size="' + str(font_size) + '" color="' + font_color + '"> ' + datetime_str + ' </font>\n'
                if len(actuall_geocoord) > 0: # if found line with geocoordinates and altitudes
                    actuall_lat = pattern_geoloc.sub(r'\2', line) + str(round(float(pattern_geoloc.sub(r'\3', line)), coord_prec))
                    actuall_lon = pattern_geoloc.sub(r'\4', line) + str(round(float(pattern_geoloc.sub(r'\5', line)), coord_prec))
                    actuall_rel_alt = pattern_rel_alt.sub(r'\1', line) + str(round(float(pattern_rel_alt.sub(r'\2', line)), 1))
                    line = pattern_geoloc.sub(r'\1', line) + 'latitude: ' + actuall_lat + '] [longitude: ' + actuall_lon +  pattern_geoloc.sub(r'\6', line)
                    if addresses_dict.get_address(actuall_lat, actuall_lon) == None:
                        # if geocoordinates don't exist in addresses_dict:
                        print('nowe współrzędne') 
                        # add geocoordinates to addresses_dict
                        actuall_geocoord = str(actuall_lat) + ', ' + str(actuall_lon)
                        actuall_location = geolocator.reverse(actuall_geocoord)
                        if actuall_location != None:
                            actuall_addr = actuall_location.address
                        else: 
                            actuall_addr = 'Adres nieznany!'
                        addresses_dict.set_address(actuall_lat, actuall_lon, actuall_addr)
                        newline_with_addr = '<font size="' + str(font_size) + '" color="' + font_color + '"> ' + actuall_addr + ' </font>' + '\n'
                        newline_with_alt = '<font size="' + str(font_size) + '" color="' + font_color + '"> ' + alt_text + actuall_rel_alt + '[m]' + ' </font>' + '\n'
                        f_tmp.write(newline_with_addr + newline_with_alt)
                    # if geocoordinates alredy exists in addresses_dict:    
                    else:
                        actuall_addr = addresses_dict.get_address(actuall_lat, actuall_lon)                 
                        newline_with_addr = '<font size="' + str(font_size) + '" color="' + font_color + '"> ' + actuall_addr + ' </font>' + '\n'
                        newline_with_alt = '<font size="' + str(font_size) + '" color="' + font_color + '"> ' + alt_text + actuall_rel_alt + '[m]' + ' </font>' + '\n'
                        f_tmp.write(newline_with_addr + newline_with_alt)     
                else:
                    f_tmp.write(line)
            f_tmp.close()
        os.remove(file_name)
        shutil.move('sub_out.txt', file_name)
        ft.close()
        os.remove('change.SRT')   
    
main()                    
        
          






