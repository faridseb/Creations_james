from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import CustomUser
from datetime import datetime
from django.contrib.auth import get_user_model
from django_countries import countries
from services.sms import send_sms  # Assurez-vous que le chemin est correct

class Command(BaseCommand):
    help = "Insère les utilisateurs avec leur parrain respectif."

    def handle(self, *args, **kwargs):
        # Création manuelle de l'admin et du leader s'ils n'existent pas
        admin, created = CustomUser.objects.get_or_create(
            username="CreationJames",
            defaults={"email": "creationjames9@gmail.com", "is_superuser": True, "is_staff": True}
        )
        leader, created = CustomUser.objects.get_or_create(
            username="James 001",
            defaults={"email": "creationjames9@gmail.com", "referrer": admin}
        )

        users_by_id = {
            1: admin,
            2: leader
        }
        # La liste complète des utilisateurs fournie (chaque ligne contient le nom et le referrer)
        data = """


3  | James0001  | 2 | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
4  | James0002  | 2 | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
5  | James0003  | 2 | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
6  | James0004  | 2 |  DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
7  | James0005  | 2 |  DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
8  | James0006  | 2 |  DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
9  | James0007  | 2 |  DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
10 | James0008  | 2 |  DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
11 | James0009  | 2 |  DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
12 | James0010  | 2 |  DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
13 | Shalom     | 3 | AKOUSSAH  | Enyonam Shalom | 1987-03-20 | Lomé | +22890720918 | Togo | 0987654321
14 | Rosalie    | 4 | KADJAWATOU  | Makiliwe Rosalie |  | Lomé | +22890353818 | Togo | 0987654321
15 | Isidore    | 5 | GBEDE  | Isidore |  | Lomé | +22890832001 | Togo | 0987654321
16 | Innocent   | 6 | ADIGO | Innocent |  | Lomé | +22890093918 | Togo | 0987654321
17 | DELAGNON   | 7 | WEISSAN |K. Delagnon  | 1978-12-31 | Lomé | +22890251764 | Togo | 0987654321
18 | TAPISSIER  | 8 | ASSRA | Koffi |  | Lomé | +22891618402 | Togo | 0987654321
19 | KAMIR      | 9 | YAYEDE NAMOINE   | Kamir | 1987-11-28 | Lomé |+22891661668  | Togo | 0987654321
20 | BASTOU     | 10|    | Bastou |  | Lomé | +22892875662 | Togo | 0987654321
21 | André      | 11| TAKAYA   | André | | Lomé | +22890257305 | Togo | 0987654321
22 | Marc       | 12|   HODABALO   | Alede Marc | 1989-12-31 | Lomé | +22890626505 | Togo | 0987654321
23 | Mamancherie| 3 | DJAMA | Adjo | 1973-12-31 | Lomé | +22899875821 | Togo |0987654321
24 | Mokpokpo   | 3 | DJONDO | Mabelle | 1998-12-31 | Tabligbo | +22899875821 | Togo | 0987654321
25 | Thibeau    | 3 | ADOUGLOU  | Koffi | 2005-07-08 |Tabligbo  | +22899875821 | Togo | 0987654321
26 | Christine  | 3 | GNASSINGBE| E. Christine | 1986-12-31 | Lomé | +22891314690 | Togo |0987654321
27 | Daria    | 3 | MENSANH | Bebe | 1969-12-18 | Lomé | +22892214985 | Togo | 0987654321
28 | Oyaba    | 3 | BLEWUSSI | Efouaboe Amavi | 1983-04-27 | Lomé | +22891574838 | Togo |0987654321
29 | Hyacinthe  | 3 | NANOUL | Hyacinte |  | Lomé | +22890170388 | Togo | 0987654321
30 | Edouard    | 3 | KOUMBIA  | Edouard |  | Lomé | +22890435254 | Togo | 0987654321
31 | AGBAHNapo  | 3 | AGBAH-Napo  |GBATI -Tchaley  |  | Lomé | +22892559162 | Togo | 0987654321
32 | Eugenie    | 3 | GNADRO | Eugenie |  | Lomé | +22892526837 | Togo | 0987654321
33 | Nikcortez  | 4 | TEHOUL | Ponipir | 1982-03-14 | Lomé | +22890063652 | Togo | 0987654321
34 | Gluck      | 4 |   HEKANOU  | Glück |  | Lomé | +22891089582 | Togo | 0987654321
35 | Dadzie     | 5 | DADZIE  | Samie |  | Lomé | +22891873712| Togo | 0987654321
36 | Gbede      | 5 | GBEDE | Kossi |  | Lomé | +22893126639 | Togo | 0987654321
37 | Pitete     | 6 | PITETE   | Essozinam |  | Lomé | +22899416096 | Togo | 0987654321
38 | Akollor    | 6 | AKOLLOR  | Kafui |  | Lomé | +22890785588 | Togo | 0987654321
39 | Gumedzoe   | 7 | GUMEDZOE  | Tonato |  | Lomé | +22890335577 | Togo | 0987654321
40 | Amedome    | 7 | AMEDOME  | kodjo  | 1968-12-31 | Lomé | +22890913488 | Togo | 0987654321
41 | Ekoue      | 8 | EKOUE  | Nicopolis |  | Lomé | +22893654708 | Togo | 0987654321
42 | Eric       | 8 | KLUTSE | Éric  |  | Lomé | +22891291530 | Togo | 0987654321
43 | Martine    | 9 | TAKETE  | Martine|  | Lomé | +22890656982 | Togo | 0987654321
44 | Marie      | 9 |  ALATCHAO  |Marie  | 1984-12-23 | Lomé | +22890612754 | Togo | 0987654321
45 | Sandrine   | 10| KARSA-TCHASSEU | Mabeba Mia | 1978-04-03 | Lomé | +22890018175 | Togo | 0987654321
46 | Bogba      | 10| DOUYEMA  | Bogra Dominique | 1950-08-04 | Lomé | +22890892458  | Togo |0987654321
47 | Amesco     | 11| SEHOU  | Amessi Kodjo | 1984-04-23 | Lomé | +22890294221 | Togo | 0987654321
48 | Kadzira    | 11| TCHIRO | Kadiratou | 1992-06-06 | Lomé | +22890987242 | Togo | 0987654321
49 | Gastino    | 12| EKLOU | Dodji Gaston | 1988-04-18 | Lomé | +22899880886 | Togo | 0987654321
50 | Cherita    | 12| ALEDA  | Essivi Débedéman| 1987-07-05 | Lomé | +22892315605 | Togo | 0987654321
51 | James 0011  |	13 | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
52 |	James 0012 |	14 |	 DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
53 |	James 0013 |	15 |	 DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
54 |	James 0014 |	16 |	 DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
55 |	James 0015 |	17 |	 DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
56 |	James 0016 |	18 | 	 DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
57 |	James 0017 |	19 |	 DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
58 |	James 0018 |	20 |	 DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
59 |	James 0019 |	21 |	 DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
60 |	James 0020 |	22 |	 DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
61 |	Elikplim 	 |51 |	GBLOKPO  | Koku Elikplim |	1991-02-20 |	Lomé |	+22893628867 |	Togo |	0987654321
62 |	BITAKO BANGOSS |	51 |	BITAKO |	Batanta Prospere |	1984-12-31 |	Lomé |	+22890820833 |	Togo | 0987654321
63 |	Lola BARARMNA |	40 | BARARMNA	|Ida Diman |	1987-11-21 |	Lomé |	+22891440518 |	Togo |0987654321
64 |	CHERITA 002 |	50 | ALEDA  | Essivi Débedéman| 1987-07-05 | Lomé | +22892315605 | Togo | 0987654321
65 |	Séraphin 2  |	51|	TENGUE 	| Kokouvi  |	1994-10-05 |	Lomé |	+22897048595 |	Togo |0987654321
66 |	Baby  |	51 |	BADJAGBO | Josephine	Baby |	1991-08-04 |	Tarkwa |	00233543656395 |	Ghana |0987654321
67 |	Api  |	51 |	APITCHAKOU | Pawimadom Essohouna Koffi |	1987-04-24 |	Lomé |	+22890972638 |	Togo |0987654321
68 |	Cecilia  |	51 | 	AHOSSEY |	Abra |	 |	Lomé |	 |+22890874546	Togo |0987654321
69 |	Elize  I |	51 |	GBEDZE |	Elize I |	1982-12-31 |	Lomé |	+22890765045 |	Togo |0987654321
70 |	Jérôme |	51 |	TOUGLO |Kodjo Ahossou |	1985-09-31 |	Lomé |	+22891597643 |	Togo |0987654321
71 |	Pierrette	| 51 |	KOUTEMA | Pierrette |	1982-12-21 |	Lomé  |	+22899880679 |	Togo |0987654321
72 | Bogardo |	51 |	DOGBOE	| Komi Bogar	 | 1985-01-05 |	Lomé |	+22890884584 | Togo |	0987654321
73 |	SAMIE |	51 |	SAMIE |	Essolakina |	1996-12-15 |	Lomé |	+22893419154 |	Togo |0987654321
74 |	Prosper |	52 |	AHIAMBLE |	Kossi |	1985-12-27 |	Lomé |	+22890944998 |	Togo |0987654321
75 |	Senator |	52 |	SAMAH |	M. Jean-pierre |	1991-09-13 |	Lomé |	+22891535877 |	Togo |0987654321
76 |	Sophie |	52 |	ABOFLAN  |	Adjovi |	1975-05-26 |	Lomé |	+22893538924 |	Togo |0987654321
77 |	Jeannette  |	52 |	AKLAMAKPE	 | Akouvi Dédé |	1991-01-05 |	Lomé |	+22892495669 |	Togo|0987654321
78 |	HENRY |	52 |	ADJANOH |	Domevenou Tekue |	1988-07-13 |	Lomé |	+22891742401 |	Togo |0987654321
79 |	rehoboth |	52 |	BOKO |	Jules |	1992-01-07 |	Lomé |	+22890532557 |	Togo |0987654321
80 |	LAMOUSSA |	52 |	LAMBONI | Lamoussa | 1982-12-30  |	Lomé |	+22890361532 |	Togo |0987654321
81 |	SABOUTEY  I |	52 |	SABOUTEY-TEYTEY I| Kossivi|	1984-11-25 |	Lomé |	+22890893605 |	Togo |0987654321
82 |	Ekpéssé 2 |	52 |	AZIABOU	|Kokou Ekpesse |	 |	Lomé |+22891826222	 |	Togo |0987654321
83 |	Gaston AGNIM 2  |	52 |	KPEKPEGNITO |	AGNIM I|	 |	Lomé |	+22891164172|	Togo |0987654321
84 |	JANOH |	52 |	Janoh |	 |	 |	Lomé |	 |	Togo |0987654321
85 |	Ayélé mimi 2 |	47 |	SEHOU  |Mimie  |	 |	Lomé |	+22890310682 |	Togo | 0987654321
86 |	Ma fille |	53 |AGBI-HELUTSE	 | Mafille|	 |	Lomé |	+22890701641 |	Togo |0987654321
87 |	Jules 002 |	79 |	BOKO |	Jules |	1992-01-07 |	Lomé |	+22890532557 |	Togo |0987654321
88 |	Jules 003 |	79 |	BOKO |	Jules |	1992-01-07 |	Lomé |	+22890532557 |	Togo |0987654321
89 |	Abé |	53 |	 |	 |	 |	Lomé |	+22892898960 |	Togo |0987654321
90 |	Sherif |	54 |	 |	 |	 |	Lomé |	+22891978283 |	Togo |0987654321
91 |	Claude |	54 |	 |	 |	 |	Lomé |	+22893529827 |	Togo |0987654321

92 |	Lookman |	55 |	 |	 |	 |	Lomé |+22890537999	 |	Togo |0987654321
93 |	Super life |	55 |	 |	 |	 |	Lomé |+22891666071	 |	Togo |0987654321
94 |	Djimdécor |	56 |	| |	 |	Lomé |+22890732050	 |	Togo |  0987654321
95 |	Mr koffi2 |	56 |	 |	|	 |	Lomé |	+22890725392 |	Togo |0987654321
96 |	Bitako02 |	62 |BITAKO |	Batanta Prospere |	1984-12-31 |	Lomé |	+22890820833 |	Togo | 0987654321
97 |	Thomas |	57 |	 |	 |	 |	Lomé |+22890145556	 |	Togo |0987654321
98 |	Thomas  02 |	97 |	 |   |	 |	Lomé | +22890145556	 |	Togo |0987654321
99 |	Bak7  |	58 |	 |  |	1990-02-18 |	Lomé |	+22890000559 |	Togo |0987654321
100 |	Godwin  |	58 |	 |	 |  |	Lomé |	+22896666593 |	Togo |0987654321
101 | Godwin 002   | 100      |     |    |    | Lomé  |  +22896666593 | Togo    | 0987654321
102 | Raymond     | 59       | Tchapo   | Raymond  |     | Lomé  |   | Togo    | 0987654321
103 | Elikplim 02        | 61       | GBLOKPO  | Koku Elikplim |	1991-02-20 |	Lomé |	+22893628867 |	Togo |	0987654321
104 | Godwin  003   | 100      |     | Godwin   |     | Lomé  |  +22896666593 | Togo    | 0987654321
105 | Godwin  004   | 100      |     | Godwin   |     | Lomé  |  +22896666593 | Togo    | 0987654321
106 | Godwin  005   | 100      |    | Godwin   |    | Lomé  | +22896666593 | Togo    | 0987654321
107 | Godwin  006   | 100      |     | Godwin   |     | Lomé  | +22896666593  | Togo    | 0987654321
108 | Daria 02           | 27       | MENSANH | Bebe | 1969-12-18 | Lomé | +22892214985 | Togo | 0987654321
109 | Daria 03           | 27       |MENSANH | Bebe | 1969-12-18 | Lomé | +22892214985 | Togo | 0987654321
110 | Daria 04           | 27       | MENSANH | Bebe | 1969-12-18 | Lomé | +22892214985 | Togo | 0987654321
111 | Jeannine           | 11       | BASSUKA |  Naka   |     | Lomé  | +22890191194  | Togo    | 0987654321
112 | Oyaba 02           | 28       |  BLEWUSSI | Efouaboe Amavi | 1983-04-27 | Lomé | +22891574838 | Togo |0987654321
113 | Yawo         | 60       |  AYITE    |  Yawo   |   | Lomé  | +23408053163997  | Togo    | 0987654321
114 | Owoussi    | 60       |     |   |    | Lomé  |+22892724368   | Togo    | 0987654321
115 | J 0021             | 4        | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
116 | J 0022             | 4        |  DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
117 | J 0023             | 4        |  DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
118 | J 0024             | 4        | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
119 | J 0025             | 4        |  DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
120 | J 0026             | 4        |  DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
121 | J 0027             | 4        |  DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
122 | J 0028             | 11       | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
123 | J 0029             | 12       | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
124 | J 0030             | 12       | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
125 | Vanosyl     | 115      |  MOUZOU  |  Sylvain  |     | Lomé  | +22898131419  | Togo    | 0987654321
126 | Jean-Paul | 115      | KANKPETI| Namipougine |  1989-02-16    | Lomé  |  +22891908445 | Togo    |  0987654321
127 | Refuge     | 115      |  AGBALI |  Atsou Mawupe  |  1981-09-05    | Lomé  | +22890749044  | Togo    | 0987654321
128 | DJAKE              | 115      |DJAKE      |      Banikiname |  1992-12-21    | Lomé  | +22893631891  | Togo    | 0987654321
129 | Komyfat    | 47       |   |  |     | Lomé  |   | Togo    | 0987654321
130 | President   | 115      | LAWSON  |  Laté Enyonam|  1977-01-31   | Lomé  | +22893160126 | Togo    |0987654321
131 | Pacôme 21/   | 115      | AGBOH    | Kossi Godgrace   |  1993-05-09  | Lomé  | +22891733555  | Togo    | 0987654321
132 | Cherif 1         | 115      |  SEI  |  Cherif   | 1992-02-25  | Lomé  |+22892391158   | Togo    | 0987654321
133 | Manassé            | 115      | MANANGA  |  Assima Claude       |   1995-09-15  | Lomé  |+22892228507   | Togo    | 0987654321
134 | Bernard            | 82       | ANLONSOU  |    Koffi Bernard     |  1996-04-12  | Lomé  | +22892184317  | Togo    | 0987654321
135 | Mawoussi           | 82       | MAWUENA | Mawussi    | 1992-12-31   | Lomé  | +22899982632  | Togo    | 0987654321
136 | Guillaume    | 82       |HODIN | Komlanvi Ameto   |  1991-06-12  | Lomé  |  +22890574429 | Togo    | 0987654321
137 | Alex  | 82    |  DEGBEVI    | KOMLANVI  |   1987-09-08  | Lomé  | +22892023454  | Togo    | 0987654321
138 | Adjatoto    | 82       | KOSSI |  Odjoutchomi Koffi F.   | 1997-07-18  | Lomé  | +22897815703  | Togo    | 0987654321
139 | Jules     | 82       | KOUDJO   | Simon  | 1965-04-12   | Lomé  |+22890293489  | Togo    | 0987654321
140 | Adèlle     | 82       |  AGBODJI  | Adele  |  1990-12-22  | Lomé  | +22892966983  | Togo    | 0987654321
141 | Ashley       | 82       |  PASSAH  |  Ablavi  |  1998-05-12   | Lomé  | +22891552722  | Togo    | 0987654321
142 | Eze   | 82       |  AKOU    | Komla    |  1999-12-31  | Lomé  | +22892903724  | Togo    | 0987654321
143 | Pascal     | 82       | NOPEGNON  | Pascal   | 1999-08-31  | Lomé  | +22891426189 | Togo    | 0987654321
144 | Yolande    | 115      | DJAHINI | Yolande   |  1970-12-17   | Lomé  |+22899515957   | Togo    | 0987654321
145 | J0043              | 51       | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
146 | Dokupé     | 45       | TEKOUTE   | Dokupé   |  1971-02-06  | Lomé  |  +22899436355 | Togo    | 0987654321
147 | EZEKIEL 74         | 48       | ATAWA  |  Wenmigaba Ezekiel     |  1974-07-08   | Lomé  |  +22890457535 | Togo    | 0987654321
148 | Daniel 001         | 48       |   |       |    | Lomé  | +22890541080  | Togo    | 0987654321
149 | Cifea          | 48       |  N'POH   |   Cifea Balobebe     |     | Lomé  |  +22891643845 | Togo    | 0987654321
150 | Poyo          | 149      |   LAGAZA  |    Angele    |  1992-01-27   | Lomé  |+22892927101   | Togo    | 0987654321
151  | Député              |  149 |  LEGUEDE  | Kossi Amegnona  | 1987-12-13  | Lomé  | +22892502244   | Togo  | 0987654321
152  | Princesse93        |  151 |  AHOSSE  |Kafui Jeanne  | 1993-05-23 | Lomé  | +22890192331 | Togo  | 0987654321
153  | Prudence            |  116 | KPONKPON   |Eya Prudence  | 1999-05-06 | Lomé  | +22898669667     | Togo  | 0987654321
154  | Jonas 90|  116 |  PAOUDE  | Patchabani |1990-08-04  | Lomé  |  +22891867705  | Togo  | 0987654321
155  | Cécile       | 116 | ANOUSSOUNGOUME   | Atame Cecile |1994-10-29   | Lomé  | +22879724625  | Togo  | 0987654321
156  | Komla  |116 | AFANVI    |  Komla Isaac |  | Lomé  | +22892153357   | Togo  | 0987654321
157  | Mawoupemon          | 116 |  AFATODJI   | Mawupemon |1998-12-31  | Lomé  |  +22893564693  | Togo  | 0987654321
158  | BIOVA               | 116 | KOUGBLENOU   |Yawa Biova  | 1996-02-15 | Lomé  |  +22892037018  | Togo  | 0987654321
159  | ESSODOM      | 116 | PEKEMSI    | ESSODOM | 1990-12-28 | Lomé  |  +22893266755  | Togo  | 0987654321
160  | Essodong    |158 |  ALITI  | Essodong |1996-06-25  | Lomé  | +22893037018   | Togo  | 0987654321
161  |  Dieudonné    |  116 | AMENIDO    |Dieudonné  |  | Lomé  |      | Togo  | 0987654321
162  | KPANTE       | 116 |  MASSASSABA  |  Kpanté|  | Lomé  | +22891476084   | Togo  | 0987654321
163  | ABLAM               | 116 | GBEKE   |  ABLAM|1992-05-17  | Lomé  |  +22899057669  | Togo  | 0987654321
164  | Richard             |  160 |   HENOU  |Bissang  | 1997-04-03 | Lomé  | +22893586792   | Togo  | 0987654321
165  | Richard 2     | 164 |  HENOU  |Bissang  | 1997-04-03 | Lomé  | +22893586792   | Togo  | 0987654321
166  | Biova 02            | 158 | KOUGBLENOU   |Yawa Biova  | 1996-02-15 | Lomé  |  +22892037018  | Togo  | 0987654321
167  | Essodong  |  160 |ALITI  | Essodong |1996-06-25  | Lomé  | +22893037018   | Togo  | 0987654321
168  | Joseph 01           | 117 |  TAHON   | Mondobozi |1988-12-31  | Lomé  |  +22891815032  | Togo  | 0987654321
169  | Joseph 02           | 168 |  TAHON   | Mondobozi |1988-12-31  | Lomé  |  +22891815032  | Togo  | 0987654321
170  | Anti       |  118 |  NABILIWA   | Baham Esso | 1995-10-07 | Lomé  | +22891401290   | Togo  | 0987654321
171  |  Kekeli     | 118 |  ADZOLOLO   | Kekili |  | Lomé  |  +22891438372   | Togo  | 0987654321
172  | Helene          | 119 |  AGO    |Pogomapazi  |  | Lomé  | +22893384718   | Togo  | 0987654321
173  | Daria 05            |108 | MENSANH | Bebe | 1969-12-18 | Lomé | +22892214985 | Togo | 0987654321
174  | Daria 06            | 174 |MENSANH | Bebe | 1969-12-18 | Lomé | +22892214985 | Togo | 0987654321
175  | Mawoupemon 02       | 157 |  AFATODJI   | Mawupemon |1998-12-31  | Lomé  |  +22893564693  | Togo  | 0987654321
176  | Akora 90            | 7   |    |  |  | Lomé  |  +22890096169  | Togo  | 0987654321
177  | Abou          | 119 |  OUDOU    | Abou | 1998-02-04 | Lomé  |   +22890455893 | Togo  | 0987654321
178  | ABRAHAHAM 2         | 163 |  GBEKE   |  ABLAM|1992-05-17  | Lomé  |  +22899057669  | Togo  | 0987654321
179  | Abou 2              |177 |  OBOU  |Oudou  |  | Lomé  | +22890455893   | Togo  | 0987654321
180  | ESSODJOLO 1         | 121 |  ESSODJOLO  | Christine |  | Lomé  |+22890533221    | Togo  | 0987654321
181  | ESSODJOLO 2         | 180 |  ESSODJOLO  | Christine |  | Lomé  |+22890533221    | Togo  | 0987654321
182  | ALIDOU          |  120 |   TELOU  |Alidou  |  | Lomé  |  +2289081812384  | Togo  | 0987654321
183  | ACHRAF              | 121 | SOULEMANA    | Achraf | 1996-12-27 |  Lomé | +22890173211 | Togo | 0987654321
184  | Judith    |      122 | TCHONDA    | Essohabe Judith| 1996-05-06 | Lomé | +22870144776 | Togo | 0987654321
185  | NASH       | 122 |NAHOURNA      |Badoguita |  | Lomé |+22892211810  | Togo | 0987654321
186  | YAYA                |123 | YAYA   | Jacques| 1997-10-04 | Lomé | +22891921399 | Togo | 0987654321
187  | Jennifer WON        | 123 |DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
188  | Augustine           | 124 | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
189  | ESSOHANA            |  124 | BADJALE    | Betema Esso-Hana| 1988-11-24 | Lomé | +22891876001 | Togo | 0987654321
190  | James 0031          |  117 | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
191  | James 0032          | 117 | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
192  | James 0033          |  117 | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
193  | James 0034          |  117 | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
194  | James 0035          |  117 | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
195  | James 0036          |  117 | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
196  | James 0037          | 117 | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
197  | James 0038          |  117 | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
198  | James 0039          |  117 |  DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
199  | James 0040          | 117 | DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
200	|GALIM mâtina  |	190  |	GALIN  |	Mahonna  |	1983-03-11  |	Lomé  |	+22893293998  |	Togo  |	0987654321
201	 |  viviane  |	190  |	AMESSIKOU   |	Viviane  |	1998-04-29  |	Lomé  |	+22893420604  |	Togo  |	0987654321
202	 | Roger	  | 190  |	EDOH  |	Mawuvi Kwami |	1978-12-30  |	Lomé  |	+22890954601  |	Togo  | 0987654321
203	 |Roger 02  |	202  |EDOH  |	Mawuvi Kwami |	1978-12-30  |	Lomé  |	+22890954601  |	Togo  | 0987654321
204	 | DONYO Adjo  |	190  |	Donyo  |	Adjo  |	1991-08-23  |	Lomé  |	+22892255029  |	Togo |	0987654321
205	 |MARDO Joséphine  |	190  |	Mardo  |	Joséphine  |	1993-10-03  |	Lomé  |	+22870137894   |	Togo  | 0987654321
206	 |Abigail  |	190  |AGBENON  |	Afiyo  |	1999-06-04  |	Lomé  |	+22879707602  |	Togo  | 0987654321
207	 |MENSAH madochée  |	190  |	Mensah  |	Madochée  |	1991-09-21  |	Lomé  |	+22897498745 |	Togo  | 0987654321
208	 |MENSAH Alain  |	190  |	Mensah  |	Alain  |	1988-05-11  |	Lomé  |	+22896349913  |	Togo  | 0987654321
209	 | wofi l  |	190  |	AMEKOU  |	Wofi Luc  |	1994-02-02  |	Lomé  |	+22890901947  |	Togo | 0987654321
210	 |AHOLOU Dossévi  |	190  |	Aholou  |	Dossévi  |	1990-03-27  |	Lomé  |	+22897025957  |	Togo  | 0987654321
211	 |AKOE Dosseh  |	190  |	Akoe  |	Dosseh  |	1993-01-14  |	Lomé  |	+22899737849  |	Togo  |	0987654321
212	 |LAMBONI Helene  |	191  |	Lamboni  |	Helene  |	1992-04-04  |	Lomé  |	+22898125732  |	Togo|	0987654321
213	 |amie  |	191  |	SEDJRO  |	Amie  |	1994-08-06  |	Lomé  |	+22896306412  |	Togo  |	0987654321
214	 |LAWSON Jacques  |	191  |	Lawson  |	Jacques  |	1989-08-28  |	Lomé  |	+22890940557 |	Togo  |	0987654321
215	 |GBEMOU   |	192  |	GBEMOU  |	Adjo |	1990-01-10  |	Lomé  |	+22890321177  |	Togo  |	0987654321
216	 |ADANLESSOSSI Bruno  |	192  |	ADANLESSOSSI  |	Bruno  |	1991-05-22  |	Lomé  |	+22892740871  |	Togo  |	0987654321
217	 |AKIM Koffi  |	193  |	AKIM  |	Koffi  |	1989-07-15  |	Kara  |	+22893004043  |	Togo  |	0987654321
218	 |AZEGLO  |	193  |	AZEGLO |	Kekeli  |	1992-03-11  |	Kpalimé  |	 +22870531494   |	Togo  |	0987654321
219	 |Antoine  |	193  |	AGBESSI |	Antoine  |	1993-08-30  |	Lomé  |	+22870440713  |	Togo  |	0987654321
220	 |Rodolphe  |	193  |	SOGBO  |	Rodolphe  |	1988-12-19  |	Sokodé  |	+22870686893  |	Togo  |	0987654321
221	 |KOFIGAN |	193  |	KOFIGAN  |	Kossi  |	1990-09-25  |	Atakpamé  |	+22890642969  |	Togo  |	0987654321
222	 |KONDI   |	193  |	KONDI  |	Aimé  |	1985-11-07  |	Dapaong  |	+22890178540  |	Togo  |	0987654321
223	 | Kwami	  |193  |	AKPE  |	Kwami  |	1994-06-14  |	Lomé  |	+22890642969  |	Togo  |	0987654321
224	 |ETSE   |	193  |	ETSE  |	Kokouvi  |	1987-10-01  |	Lomé  |	+22898649855  |	Togo  |	0987654321
225	 |Remi  |	194  |	AGBENOU  |	Remi  |	1991-01-12  |	Lomé  |	+22890517299 |	Togo  |	0987654321
226	 |TOSSOU 	  | 194	  |TOSSOU  |	Victor  |	1992-04-23  |	Lomé  |	+22897497572  |	Togo  |	0987654321
227	 |HALO   |195  |	HALO |	Mawuli |	1986-06-18 |	Lomé |	+22892817294 |	Togo |	0987654321
228	 |TCHALEGAN   |	195 |	TCHALEGAN |	M’beti |	1989-11-04 |	Sokodé |	+22896621708 |	Togo |	0987654321
229	 | Chantale |	196 | 	KOMANDA |	Chantale |	1993-05-15 |	Lomé |	+22898751788 | 	Togo |	0987654321
230	 | Bileyo |	196 |	KATAO |	Bileyo |	1990-07-22 |	Lomé |	+22890324045 |	Togo |	0987654321
231	 | Magloire |	196 | 	AGBO |	Magloire |	1991-12-30 |	Aného |	+22890669258 |	Togo |	0987654321
232	 | HOVIDE  |	196 |	HOVIDE |	Joël | 1988-09-09 |	Lomé |	+22890838417 |	Togo |	0987654321
233	 | Lynne |	196 |	BLIKINE |	Lynne |	1995-01-05 |	Kpalimé |	+22890600302 |	Togo |	0987654321
234	 |RAKMAN  |	196 |	RAKMAN |	Idrissou |	1992-02-20 |	Kara |	+22891851097 |	Togo |	0987654321
235	 | Ashley |	196 | 	AKAKPOVI |	Ashley |	1993-03-03 |	Lomé |	 +22899011564 |	Togo |	0987654321
236	 |Nestor  |	206 |	HOUNGBESSO |	Nestor |	1985-05-25 |	Dapaong |	+22879959260 |	Togo |	0987654321
237	 |AGBENON Abigail 02 |	206 | 	AGBENON |	Abigail |	1994-07-17 |	Lomé |	+22879707602 |	Togo |	0987654321
238	 |PATA | 	206 |	PATA |	Aglouzou |	1986-10-12 |	Sokodé |	+22891643883 |	Togo |	0987654321
239	 |DADY  |	229 | 	DADY |	Houmawo Tseluto|	1991-09-18 |	Lomé |	+22899221350 |	Togo |	0987654321
240	 |KOUDJO |	231 | 	KOUDJO |		| 1992-06-29 |	Lomé |	+22897595765 |	Togo |	0987654321
241	 |James 0041 | 	197 |	 DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
242	 |James 0042 |	198 |	 DJAMESSI    | koffi amegnon| 1984-12-31 | Lomé | +22890121764 | Togo | 0987654321
243	 |HOUNGBESSO Nestor 02 |	236 |	HOUNGBESSO |	Nestor |	1985-05-26 |	Dapaong	 |+22890920112 |	Togo |	0987654321
244	 |RAJ |	199 |	RAJ	 |	| 1987-04-21 |	Lomé |	+22890021223 |	Togo |	0987654321
245	 |RAJ 02 |	244 |	RAJ |	 |	 1987-04-21 |	Lomé |	+22890021223 |	Togo |	0987654321
246	 | Sékou |	241 | 	KONATARE |	Sékou |	1992-11-30 |	Kara |	 |	Togo |	0987654321
247	 | Shawad |	208 |	KOKOU |	Shawad |	1994-08-19 |	Lomé |	+22899560198 |	Togo | 	0987654321
248	 | parnine |	241 |N.Gomna	 |	Parnine |	1989-09-10 |	Dapaong |+22899756792	  |	Togo |	0987654321
249	 | Deborah |	241 |	PIGNANDI |	Deborah	| 1990-10-01 |	Lomé |	+22898507413 |	Togo |	0987654321
250	 |Baudouin |	241 |	DJEDU |	Baudown |	1986-06-06 |	Lomé |	+22891004178 |	Togo |	0987654321
251	 |Prince OGABE |	241 |	OGABE |	Prince |	1991-03-15 |	Lomé |	+22890136143 | 	Togo |	0987654321

        """
        User = get_user_model()

        def get_country_code_from_name(country_name):
            for code, name in countries:
                if name.lower() == country_name.lower():
                    return code
            return None

        # Vérification de validité du numéro
        def is_valid_phone_number(phone):
            pattern = r'^\+\d{8,15}$'  # +22890136143, +33600000000, etc.
            return bool(re.match(pattern, phone))
        rows = data.strip().split("\n")

        for index, row in enumerate(rows, start=1):
            fields = [f.strip() for f in row.strip().split('|')]

            if len(fields) < 10:
                self.stdout.write(
                    self.style.WARNING(
                        f"Ligne {index} incomplète ({len(fields)} champs) : {row}"
                    )
                )
                continue  # On saute cette ligne

            username = fields[1] or None
            referrer_id = fields[2]
            nom = fields[3] or ""
            prenom = fields[4] or ""
            date_str = fields[5]
            ville = fields[6] or ""
            contact = fields[7] or ""
            country_name = fields[8] or ""
            password = fields[9] or "default_password"

            # Convertir nom du pays en code (ex: "Togo" → "TG")
            country = get_country_code_from_name(country_name) or ""

            # Gérer referrer
            referrer = None
            if referrer_id:
                try:
                    referrer = User.objects.get(id=int(referrer_id))
                except (User.DoesNotExist, ValueError):
                    referrer = None

            # Gérer date de naissance
            date_of_birth = None
            if date_str:
                try:
                    date_of_birth = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    date_of_birth = None

            # Vérifier que le username est fourni
            if username and not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f" ",
                    nom=nom,
                    prenom=prenom,
                    date_of_birth=date_of_birth,
                    ville=ville,
                    contact=contact,
                    country=country,  # code ISO comme "TG"
                    referrer=referrer,
                    password=password  # Hashé automatiquement
                )
                self.stdout.write(self.style.SUCCESS(f"Utilisateur {username} créé avec succès."))
                commission_parrain = Decimal('500')

                if referrer:
                    # Récompense pour le parrain
                    if hasattr(referrer, 'wallet'):
                        referrer.wallet.balance += commission_parrain
                        referrer.wallet.save()

                        # Enregistrement de la transaction
                        Transaction.objects.create(
                            user=referrer,
                            amount=commission_parrain,
                            reason=f"Paiement de commission pour l'inscription de {user.username}",
                            is_successful=True
                        )
                        self.stdout.write(self.style.SUCCESS(
                            f"Commission de 500 FCFA ajoutée au portefeuille de {referrer.username}."))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"Parrain {referrer.username} n'a pas de wallet. Commission non créditée."))
                # Message de bienvenue à l'utilisateur
                message_for_user = (
                    f"Bonjour {user.username},\n"
                    f"Votre inscription sur notre plateforme a bien été prise en compte.\n"
                    f"Bienvenue parmi nous !"
                )
                if is_valid_phone_number(user.contact):
                    send_sms(user.contact, message_for_user)
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Numéro invalide ou manquant pour {user.username}. SMS non envoyé."))

                # Message au parrain (si présent)
                if referrer:
                    message_for_referrer = (
                        f"Bonjour {referrer.username},\n"
                        f"Votre filleul {user.username} vient de s’inscrire avec succès.\n"
                        f"Vous avez reçu une commission de 500 FCFA\n"
                        f"pour l'inscription de votre filleul {user.username}.\n"
                        f"Merci pour votre parrainage !"
                    )
                    if is_valid_phone_number(referrer.contact):
                        send_sms(referrer.contact, message_for_referrer)
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Numéro invalide ou manquant pour le parrain de {user.username}."))
            else:
                self.stdout.write(
                    self.style.WARNING(f"Utilisateur {username} existe déjà ou nom d'utilisateur manquant.")
                )
