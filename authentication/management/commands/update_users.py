from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import CustomUser

import re
class Command(BaseCommand):
    help = "Met à jour les parrains des utilisateurs depuis une liste prédéfinie."
    def handle(self, *args, **kwargs):
        # La liste complète des utilisateurs fournie (chaque ligne contient le nom et le referrer)
        data = """


3.   James 0001  REFERRER : 2
4.   James 0002  REFERRER : 2
5.   James 0003  REFERRER : 2
6.   James 0004  REFERRER : 2
7.   James 0005  REFERRER : 2
8.   James 0006  REFERRER : 2
9.   James 0007  REFERRER : 2
10.  James 0008  REFERRER : 2
11.  James 0009  REFERRER : 2
12.  James 0010  REFERRER : 2
13.  Shalom     REFERRER : 3
14.  Rosalie    REFERRER : 4
15.  Isidore    REFERRER : 5
16.  Innocent   REFERRER : 6
17.  DELAGNON   REFERRER : 7
18.  TAPISSIER  REFERRER : 8
19.  KAMIR      REFERRER : 9
20.  BASTOU     REFERRER : 10
21.  André      REFERRER : 11
22.  Marc       REFERRER : 12
23.  Maman chérie   REFERRER : 3
24.  Mokpokpo       REFERRER : 3
25.  Thibeau        REFERRER : 3
26.  Christine      REFERRER : 3
27.  Daria II       REFERRER : 3
28.  Oyaba II       REFERRER : 3
29.  Hyocinthe      REFERRER : 3
30.  Edouard        REFERRER : 3
31.  AGBAH Napo Tchaley   REFERRER : 3
32.  Eugenie        REFERRER : 3
33   Nikcortez             REFERRER : 4
34.  Glück                 REFERRER : 4
35.  DADZIE SAMIE   REFERRER : 5
36.  GBEDE kossi    REFERRER : 5
37.  PITETE         REFERRER : 6
38.  AKOLLOR makafui       REFERRER : 6
39.  GUMEDZOE Tonato       REFERRER : 7
40.  AMEDOME kodjo II      REFERRER : 7
41.  EKOE Nicopolis        REFERRER : 8
42.  Éric Klutsè           REFERRER : 8
43.  Martine               REFERRER : 9
44.  Marie                 REFERRER : 9
45.  K. Sandrine           REFERRER : 10
46.  BOGBA Djouyéma II      REFERRER : 10
47.  AMESCO dodo           REFERRER : 11
48.  KADZIRATOU            REFERRER : 11
49.  GASTINO II            REFERRER : 12
50.  CHERITA               REFERRER : 12
51.  James 0011            REFERRER : 13
52.  James 0012            REFERRER : 14
53.  James 0013            REFERRER : 15
54.  James 0014            REFERRER : 16
55.  James 0015            REFERRER : 17
56.  James 0016            REFERRER : 18
57.  James 0017            REFERRER : 19
58.  James 0018            REFERRER : 20
59.  James 0019            REFERRER : 21
60.  James 0020            REFERRER : 22
61.  Elikplim II           REFERRER : 51
62.  BITAKO BANGOSS        REFERRER : 51
63.  Lola BARARMNA         REFERRER : 40
64.  CHERITA 002           REFERRER : 50
65.  Séraphin II           REFERRER : 51
66.  Baby Joséphine II     REFERRER : 51
67.  Api Pawissatom        REFERRER : 51
68.  Cecilia RT            REFERRER : 51
69.  Elize dame pagne II   REFERRER : 51
70.  Jérôme maçon          REFERRER : 51
71.  Pierrette             REFERRER : 51
72.  Edouard Bogardo       REFERRER : 51
73.  Essolakina SAMIE      REFERRER : 51
74.  Prosper               REFERRER : 52
75.  Sendter               REFERRER : 52
76.  Sophie                REFERRER : 52
77.  Jeannette dédé        REFERRER : 52
78.  HENRISON              REFERRER : 52
79.  Jules                 REFERRER : 52
80.  LAMOUSSA              REFERRER : 52
81.  SABOUTEY II           REFERRER : 52
82.  Ekpéssé II            REFERRER : 52
83.  Gaston AGNIM II       REFERRER : 52
84.  JANOH                 REFERRER : 52
85.  Ayélé mimi II         REFERRER : 47
86.  Ma fille              REFERRER : 53
87.  Jules 002             REFERRER : 79
88.  Jules 003             REFERRER : 79
89.  Abé                   REFERRER : 53
90.  Sherif                REFERRER : 54
91.  Claude                REFERRER : 54
92.  Lookman               REFERRER : 55
93.  Super life            REFERRER : 55
94.  Djim décor            REFERRER : 56
95.  Mr koffi II           REFERRER : 56
96.  Bitako 02             REFERRER : 62
97.  Thomas mécano         REFERRER : 57
98.  Thomas mécano 02      REFERRER : 97
99.  Bak 7 William         REFERRER : 58
100. Godwin koffi          REFERRER : 58
101. Godwin koffi 002      REFERRER : 100
102. Raymond Tchapo        REFERRER : 59
103. Elikplim 02           REFERRER : 61
104. Godwin koffi 003      REFERRER : 100
105. Godwin koffi 004      REFERRER : 100
106. Godwin koffi 005      REFERRER : 100
107. Godwin koffi 006      REFERRER : 100
108. Daria 02              REFERRER : 27
109. Daria 03              REFERRER : 27
110. Daria 04              REFERRER : 27
111. Jeannine              REFERRER : 11
112. Oyaba 02              REFERRER : 28
113. Yawo ayite            REFERRER : 60
114. Cervo / Owoussi       REFERRER : 60
115. J 0021                REFERRER : 4
116. J 0022                REFERRER : 4
117. J 0023                REFERRER : 4
118. J 0024                REFERRER : 4
119. J 0025                REFERRER : 4
120. J 0026                REFERRER : 4
121. J 0027                REFERRER : 4
122. J 0028                REFERRER : 11
123. J 0029                REFERRER : 12
124. J 0030                REFERRER : 12
125. Vanosy/ mouzou        REFERRER : 115
126. Jean-Paul/ KANKPETI     REFERRER : 115
127. Refuge/ AGBALI        REFERRER : 115
128. AJAKE                 REFERRER : 115
129. Komyfat Tchangai       REFERRER : 47
130. Président Lawson      REFERRER : 115
131. Pacôme 21/ AGBOH       REFERRER : 115
132. SEI Sherif            REFERRER : 115
133. Manassé               REFERRER : 115
134. Bernard               REFERRER : 82
135. Mawoussi              REFERRER : 82
136. Guillaume Asdin       REFERRER : 82
137. Alex le bleu/ Degbevi  REFERRER : 82
138. Adjatoto/ kossi       REFERRER : 82
139. Jules konafo          REFERRER : 82
140. Adèlle AGBODZI        REFERRER : 82
141. Ashley Passah         REFERRER : 82
142. Eze Akou              REFERRER : 82
143. Pascal NOPEGNON       REFERRER : 82
144. Yolanda DJAHINI       REFERRER : 115
145. J0043                 REFERRER : 51
146. Dokupé/ TEKOUTE       REFERRER : 45
147. EZEKIEL 74 II         REFERRER : 115
148. Dodji le roi / TCHOTEBA REFERRER : 115
149. CIPEA                 REFERRER : 116
150. Poyo                  REFERRER : 149
151. Député               REFERRER : 149
152. Princesse            REFERRER : 151
153. Prudence             REFERRER : 116
154. Jonas PAOUDE Solim    REFERRER : 116
155. Cécile Acetone       REFERRER : 116
156. Komla Isaac AFANVI   REFERRER : 116
157. Mawoupemon           REFERRER : 116
158. BIOVA                REFERRER : 116
159. Freddy PEKEMSI       REFERRER : 116
160. Essodong maxwell     REFERRER : 158
161. AMANDO Dieudonné     REFERRER : 116
162. KPANTE MASS          REFERRER : 116
163. ABLAM                REFERRER : 116
164. Richard              REFERRER : 160
165. Richard Henou 1      REFERRER : 164
166. Biova 02             REFERRER : 158
167. Essodong maxwell 02  REFERRER : 160
168. Joseph 01            REFERRER : 117
169. Joseph 02            REFERRER : 168
170. Anti NABILIWA        REFERRER : 118
171. ADZOLOLO Kekeli      REFERRER : 118
172. Helene AHO           REFERRER : 119
173. Daria 05             REFERRER : 108
174. Daria 06             REFERRER : 174
175. Mawoupemon 02        REFERRER : 157
176. Akora 90             REFERRER : 7
177. OUDOU Abou           REFERRER : 119
178. ABRAHAHAM 2          REFERRER : 163
179. Abou 2               REFERRER : 177
180. ESSODJOLO 1          REFERRER : 121
181. ESSODJOLO 2          REFERRER : 180
182. ALIDOU K             REFERRER : 120
183. ACHRAF               REFERRER : 121
184. Justine TCHONDA      REFERRER : 122
185. NASH NAHOURNA        REFERRER : 122
186. YAYA                 REFERRER : 123
187. Jennifer WON         REFERRER : 123
188. Augustine            REFERRER : 124
189. ESSOHANA             REFERRER : 124
190. James 0031           REFERRER : 117
191. James 0032           REFERRER : 117
192. James 0033           REFERRER : 117
193. James 0034           REFERRER : 117
194. James 0035           REFERRER : 117
195. James 0036           REFERRER : 117
196. James 0037           REFERRER : 117
197. James 0038           REFERRER : 117
198. James 0039           REFERRER : 117
199. James 0040           REFERRER : 117
200. GALIM mâtina         REFERRER : 190
201. AMESSIKOU viviane    REFERRER : 190
202. EDOH Roger           REFERRER : 190
203. EDOH Roger 02        REFERRER : 202
204. DONYO Adjo           REFERRER : 190
205. MARDO Joséphine      REFERRER : 190
206. AGBENON Afiyo        REFERRER : 190
207. MENSAH madochée      REFERRER : 190
208. MENSAH Alain         REFERRER : 190
209. AMEKOU wofi luc      REFERRER : 190
210. AHOLOU Dossévi       REFERRER : 190
211. AKOE Dosseh          REFERRER : 190
212. LAMBONI Helene       REFERRER : 191
213. SEDJRO Abigail       REFERRER : 191
214. LAWSON Jacques       REFERRER : 191
215. GBEMOU Adjo          REFERRER : 192
216. ADANLESSOSSI Bruno   REFERRER : 192
217. AKIM Koffi           REFERRER : 193
218. AZEGLO Kekeli        REFERRER : 193
219. AGBESSI Antoine      REFERRER : 193
220. SOGBO Koffi Rodolphe REFERRER : 193
221. KOFIGAN Kossi        REFERRER : 193
222. KONDI Aimé           REFERRER : 193
223. AKPE Kwami           REFERRER : 193
224. ETSE Kokouvi         REFERRER : 193
225. AGBENOU Remi         REFERRER : 194
226. TOSSOU Victor        REFERRER : 194
227. HALO Mawuli          REFERRER : 195
228. TCHALEGAN M’beti     REFERRER : 195
229. KOMANDA Chantale     REFERRER : 196
230. KATAO Bileyo         REFERRER : 196
231. AGBO AGBO ma gloire  REFERRER : 196
232. HOVIDE ayefui Joël   REFERRER : 196
233. BLIKINE Lynne        REFERRER : 196
234. RAKMAN Idrissou      REFERRER : 196
235. AKAKPOVI Ashley      REFERRER : 196
236. Nestor HOUNGBESSO    REFERRER : 206
237. AGBENON Abigail 02    REFERRER : 206
238. PATA Aglouzou        REFERRER : 206
239. DADY Houmawo Tseluto  REFERRER : 229
240. KOUDJO               REFERRER : 231
241. James 0041           REFERRER : 197
242. James 0042           REFERRER : 198
243. HOUNGBESSO Nestor 02 REFERRER : 236
244. RAJ                  REFERRER : 199
245. RAJ 02               REFERRER : 244
246. KONATARE Sékou       REFERRER : 241
247. KOKOU Shawael        REFERRER : 208
248. N.Gomna parnine      REFERRER : 241
249. PIGNANDI Deborah     REFERRER : 241
250. DJEDU Baudown        REFERRER : 241
251. Prince OGABE         REFERRER : 241

        """
        pattern = re.compile(r"(\d+)\.\s+(.+?)\s+REFERRER\s+:\s+(\d+)")
        matches = pattern.findall(data)

        if not matches:
            self.stdout.write(self.style.WARNING("Aucune correspondance trouvée dans les données fournies."))
            return

        updated_count = 0

        for user_id, username, referrer_id in matches:
            try:
                user = CustomUser.objects.get(id=int(user_id))
                referrer = CustomUser.objects.get(id=int(referrer_id))
                user.referrer = referrer
                user.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Mise à jour réussie : {user.username} -> Parrain {referrer.username}"))
            except CustomUser.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Utilisateur ou parrain non trouvé pour ID {user_id} ou {referrer_id}"))

        self.stdout.write(self.style.SUCCESS(f"{updated_count} utilisateurs mis à jour."))
