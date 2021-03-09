import os

CACHE_PATH = "data_cache"

if 'DYNO' in os.environ:     # heroku env
    GOOGLE_CHROME_PATH = '/app/.apt/usr/bin/google_chrome'
    CHROMEDRIVER_PATH = '/app/.chromedriver/bin/chromedriver'
else:                        # local env
    GOOGLE_CHROME_PATH = ''
    CHROMEDRIVER_PATH = "src/chromedriver_upd"

LIST_OF_YEARS = [2020, 2019, 2018, 2017, 2016, 2015, 2014]

LIST_OF_COUNTRIES = ["<Choix d'un pays>", "France", "Espagne",
                     "Angleterre", "Allemagne", "Italie"]

CHOIX_TEAMS = ["<Choix d'un pays>"]

FRENCH_TEAMS = ["<Choix d'une équipe>", "Lille", "Lyon", "Paris_Saint_Germain",
                "Monaco", "Lens", "Metz", "Marseille",
                "Rennes", "Lorient", "Strasbourg",
                "Montpellier", "Bordeaux", "Nice", "Brest",
                "Angers", "Nantes", "Reims", "Nantes",
                "Dijon", "Nimes"]

GERMAN_TEAMS = ["<Choix d'une équipe>", 'Werder_Bremen', 'VfB_Stuttgart', 'Union_Berlin', 'Schalke_04',
                'RasenBallsport_Leipzig', 'Mainz_05', 'Hoffenheim',
                'Hertha_Berlin', 'Freiburg', 'FC_Cologne', 'Eintracht_Frankfurt',
                'Borussia_M.Gladbach', 'Borussia_Dortmund', 'Bayern_Munich',
                'Bayer_Leverkusen', 'Augsburg', 'Arminia_Bielefeld']

ENGLISH_TEAMS = ["<Choix d'une équipe>", 'Manchester_City', 'Manchester_United', 'Leicester', 'West_Ham', 'Chelsea',
                 'Liverpool', 'Everton', 'Aston_Villa', 'Tottenham', 'Leeds',
                 'Arsenal', 'Wolverhampton_Wanderers', 'Crystal_Palace',
                 'Southampton', 'Burnley', 'Brighton', 'Newcastle_United', 'Fulham',
                 'West_Bromwich_Albion', 'Sheffield_United']

SPANISH_TEAMS = ["<Choix d'une équipe>", 'Atletico_Madrid', 'Real_Madrid', 'Barcelona', 'Sevilla',
                 'Real_Sociedad', 'Villarreal', 'Real_Betis', 'Levante', 'Granada',
                 'Athletic_Club', 'Celta_Vigo', 'Valencia', 'Osasuna', 'Cadiz',
                 'Getafe', 'Alaves', 'Eibar', 'Real_Valladolid', 'Elche',
                 'SD_Huesca']

ITALIAN_TEAMS = ["<Choix d'une équipe>", 'Inter', 'AC_Milan', 'Juventus', 'Roma', 'Atalanta', 'Lazio',
                 'Napoli', 'Sassuolo', 'Verona', 'Sampdoria', 'Genoa', 'Bologna',
                 'Udinese', 'Fiorentina', 'Benevento', 'Spezia', 'Torino',
                 'Cagliari', 'Parma_Calcio_1913', 'Crotone']

COUNTRY_TEAMS = {"France": FRENCH_TEAMS,
                 "Espagne": SPANISH_TEAMS,
                 "Angleterre": ENGLISH_TEAMS,
                 "Allemagne": GERMAN_TEAMS,
                 "Italie": ITALIAN_TEAMS,
                 "<Choix d'un pays>": CHOIX_TEAMS}
