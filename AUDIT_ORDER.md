# AUDIT ORDER — zlecenie audytu tego repozytorium

Dokument zamawia audyt; sam audytem nie jest. Obowiązuje od commita, który go
wprowadza, do przyjęcia raportu — potem znika razem z nim, bo plik bez nazwanego
celu nie zostaje w tym drzewie (`AGENTS.md` § Values, *Minimalism*).

Repozytorium nie ma testów, CI ani lintera i **nie jest to dług** — to decyzja
zapisana w `AGENTS.md` § Values („*Destination, not road*"). Jedyny mechanizm
kontroli jakości, jaki ta konstytucja dopuszcza, to **audyt czytelniczy**: etap
dowodzi się tym, że biegnie, a wszystko poza nim — tym, że ktoś przeczytał kod
wobec kontraktu. To zlecenie formalizuje ten mechanizm.

## Mandate

| pozycja | wartość |
|---|---|
| przedmiot | `902-LIORA-MLOps-Portfolio-Data-Dashboard-Single-Asset`, gałąź `main` |
| stan | HEAD `c996e41`, 17 commitów, drzewo czyste |
| objętość | 72 pliki śledzone, 11 736 linii |
| dokumenty normatywne | `AGENTS.md`, `module_skills/glossary.md`, 10 skilli |
| dowód działania | `store_run_records/20260830T153012Z_c2b1a74/` — 4134 surowe ZIP-y, 2 976 480 kanonicznych minut, komplet artefaktów BTC |
| produkt | jeden raport wedle § *What counts as a finding* |

**Pytanie audytowe: czy implementacja robi to, do czego zobowiązuje ją jej własny
kontrakt.** Nie: czy spełnia standardy zewnętrzne, których to repozytorium
świadomie nie przyjęło.

Zakres pokrycia deklaruje się **per moduł**, nie per plik. Drzewem jest
`git ls-files`; spis plików w tym dokumencie byłby drugą kopią, która się
rozjedzie (`AGENTS.md` § The default choice).

## What counts as a finding

Znaleziskiem jest **rozjazd między dokumentem a kodem**. Skala jest zdefiniowana
kontraktem, nie ryzykiem produkcyjnym:

| stopień | znaczenie |
|---|---|
| **contract breach** | kod robi co innego, niż wiąże `AGENTS.md` albo skill — w tym każdy przypadek, gdzie dokument deklaruje własność, której kod nie ma |
| **drift** | dwa miejsca opisują tę samą rzecz i się rozjeżdżają, albo reguła jest spełniona przypadkiem, a nie z konstrukcji |
| **note** | obserwacja bez naruszenia. Nota **musi nazwać decyzję i jej właściciela**, inaczej jest odłożoną decyzją, czyli tym samym co znacznik długu, którego `AGENTS.md` § Values zabrania. Noty żyją i umierają z raportem — żadna nie wchodzi do pliku śledzonego |

**Łańcuch pierwszeństwa — którą stronę się rusza.** Bez niego żadne znalezisko
klasy *drift* nie da się rozstrzygnąć. `AGENTS.md` rozstrzyga siebie wobec kodu
(„*If a change conflicts with this file, the change is wrong*"); reszta wynika
z ownershipu:

```
AGENTS.md  >  skill modułu, który jest właścicielem reguły
           >  README_module_<name>.md
           >  kod
```

Każde znalezisko wskazuje, **która strona się rusza**.

### Czego audyt nie zgłasza

Bezpieczeństwo, powierzchnia ataku i hardening są **poza zakresem**. Raport,
który je porusza, jest w tej części odrzucany. Nie są znaleziskami żadnego
stopnia: brak testów, brak CI, brak lintera, brak auth, CSRF, brak CORS, brak
rate-limitu, brak healthchecku, brak polityki restartu, „root-equivalent docker
socket".

Powody, i to jest cała argumentacja:

- **To aplikacja akademicka.** Pokazuje, *jak taki system działa*; dowodem jest
  przebiegnięty łańcuch i zostawione artefakty, nie zielony pasek testów
  (`AGENTS.md` § Values, *Academic, not production*).
- **Guardraile są policzone i zamknięte.** Konstytucja dopuszcza dokładnie
  **siedem guardów, których wymaga matematyka** (`AGENTS.md` § Values), i nic
  poza nimi. Brak walidacji obronnej nie jest brakiem — jest regułą.
- **Wektor wejścia jest znany, opisany i przyjęty.**
  `module_monitoring/skills/skill_devops_panel.md` § The one socket, and what
  containment means nie udaje, że go nie ma: kontenowany jest *mount*, nie
  *zasięg*, a „*any client that can reach the dashboard's loopback origin can
  reach the Engine through the proxy*". To jest zapisane, nie przeoczone —
  „*Stated, not mitigated*".
- **Przyjęty, bo nie ma za nim nic.** Żadnych poświadczeń: obie giełdowe API są
  publiczne i bezkluczowe, nie ma `.env`, nie ma sekretu w compose. Żadnych
  danych osobowych. Żadnego kapitału — `BTC_strategy_evaluation.json` to wynik
  badawczy, którego końcowy holdout wychodzi na minus i jest tak raportowany,
  a nie działające rozwiązanie transakcyjne. Zasięg rażenia to `start`, `stop`
  i `restart` na własnych kontenerach operatora.
- **Reszta drogi leży poza tym drzewem.** Dashboard jest publikowany wyłącznie
  na `127.0.0.1`, `portraefik` nie publikuje żadnego portu. Żeby dosięgnąć
  loopbacku, trzeba najpierw złamać SSH między użytkownikiem a chmurą albo samą
  chmurę — a to problem systemowy, który dotyczy wszystkich naraz, nie defekt
  tego kodu. Projektowanie pod niego byłoby projektowaniem pod problem, którego
  nie mamy jak mieć.

**Co mimo to zostaje w zakresie**, i wyłącznie jako pytanie o zgodność, bo skill
te własności *deklaruje*: allowlist trzech czasowników, fail-closed guard na
etykiecie `com.docker.compose.project`, i jeden socket w jednej usłudze
(`AGENTS.md` § Rejected vocabulary).

## Method and evidence

1. **Czytać w kolejności narzuconej przez `AGENTS.md`** (preambuła):
   `AGENTS.md` → nazwy modułów → `README_module_<name>.md` → `skills/` modułu →
   kod. `README.md` nie leży na ścieżce roboczej.
2. **Cytować jak repozytorium**: ścieżka + sekcja (`glossary.md § Artifacts`)
   albo ścieżka + symbol (`indicators.asof_index`). **Nigdy `plik:linia`** —
   żaden śledzony markdown w tym drzewie nie używa kotwic liniowych, a nowa
   konwencja musi spełnić siedem warunków z
   `module_skills/skill_self_explaining_naming.md` § Minting a new convention
   i wejść do `AGENTS.md` w tym samym commicie.
3. **Odtworzyć łańcuch**: `make docker-build && make docker-all-record`.
   Parytetem jest **tabela etapów** (które etapy, w której usłudze, w jakiej
   kolejności, z jakim kodem wyjścia) i sumy kontrolne artefaktów — **nie**
   liczby z `summary.json`: `run_id` niesie znacznik czasu i commit, a czasy
   ścianowe, `orchestration_seconds` i `bottleneck_stage` nie są odtwarzalne
   z definicji.
4. **Test parytetu bitowego**: dwa przebiegi `make ml-all`, porównać sumy
   kontrolne artefaktów — z wyłączeniem plików niosących `generated_at_utc`
   i pliku `.duckdb` (`module_skills/skill_determinism.md` wiąże parytet
   z tym samym kodem, oknem i środowiskiem; `glossary.md` zakres bajtowy
   przypisuje README aktywa, nie bazie).
5. **Świeżość rysunku DX** — gate, nie ciekawostka:
   `python3 -m module_monitoring.sub_module_dx.visualise --check`. Regeneruje
   w pamięci i porównuje; wychodzi 1 przy rozjeździe. Celowo bez celu
   w Makefile. **Uruchomić na commicie poprzedzającym to zlecenie** — samo
   dodanie pliku śledzonego zmienia drzewo, więc po tym commicie check musi
   zostać domknięty przez `make monitoring-dx-update`.

## Scope — the main tree

- `Makefile` — gramatyka `<module>-<stage>` / `docker-<module>-<stage>`; bare
  target wyłącznie lifecycle (`AGENTS.md` § Canonical vocabulary). Aliasy
  `docker-btc-all` i `docker-btc-lifecycle` same deklarują, że znikają, gdy
  koszyk urośnie — czy warunek już zaszedł.
- `docker-compose.yml` — czy usługi są nadal wypisane jawnie pod dwiema
  kotwicami, a nie generowane (`AGENTS.md` § Canonical vocabulary,
  *Rule-derived structure*); czy `portraefik` nadal nie publikuje portu.
- `requirements.txt` — wyłącznie zależności bezpośrednie, każda z nazwanym
  zastosowaniem (`AGENTS.md` § Values, *Minimum requirements*).
- `.gitignore` — czy „derived, never drafted" trzyma: śledzone są tylko
  `<TICKER>_parameters.json` i `<TICKER>_README.md`, oba generowane
  (`AGENTS.md` § Canonical vocabulary). Ręczna edycja któregokolwiek jest
  naruszeniem.
- `store_*` — trzy katalogi, jeden blok w listingu; czy porządek taksonomiczny
  nadal zachodzi (`AGENTS.md` § Architecture shape).

## Scope — module_data

Odpowiedzialność kończy się na kanonicznym obiekcie 1m.

- **Kontrakt kanonizacji.** Świeca kanoniczna to **cała** świeca jednej giełdy
  albo oflagowany `ffill` — nigdy kompozyt pole-po-polu, nigdy średnia
  (`skill_candle_canonicalisation.md` § 5, § 6, § 7). Czy jeden
  `CANONICAL_INSERT` w `ingest.py` realnie zamyka całą tabelę decyzyjną.
- **Niezmienniki.** `duplicate_count == 0` i `ohlc_violation_count == 0` to
  jedyne dwie liczby o randze pass/fail (`skill_candle_canonicalisation.md`
  § 16). Czy nic innego do tej rangi nie awansowało.
- **Idempotencja.** Pomijanie dnia po obecności pliku i pełna przebudowa bazy
  przy każdym `ingest`. Uwaga: `skill_candle_canonicalisation.md` § 17
  i `methodology_data.md` deklarują idempotencję **plikową**, nie bajtową —
  `lean.write_lean_zip` stempluje ZIP lokalnym zegarem. Sprawdzić, czy któryś
  dokument obiecuje więcej.
- **Asymetria liczenia ZIP-ów** — `status.py` liczy samym globem,
  `ingest.load_zip_paths` dokłada regex nazwy. Obcy `*_trade.zip` byłby
  policzony przez jedno i zignorowany przez drugie: która strona się rusza.
- **Pusta unia venue'ów** — `ingest.main` liczy koniec siatki jako
  `max(timestamp_ms) + 60000`; na tickerze bez pobranych ZIP-ów daje goły
  `TypeError` zamiast jednoliniowego komunikatu etapu, którego chce
  `AGENTS.md` § Values.

## Scope — module_ml

### Leakage
Potwierdzić albo obalić, każde z osobna — wszystkie są deklaracjami
`methodology_ml.md` § 1 (*the nine rules the code implements*):

- purge to `event_end_ts <= oos_start` z wyłącznym końcem
  (`validation.training_set`);
- dopuszczenie do scoringu jest **rozstrzygalne w t₀**
  (`entry_ts + horyzont <= oos_end`), a nie po faktycznym, ścieżkowo zależnym
  `event_end_ts` (`validation.scoring_set`) — i ta sama reguła rządzi
  kwalifikacją wejścia w `strategy.backtest`;
- wagi average-uniqueness mierzone **na populacji, która ich używa**, a nie raz
  globalnie (`validation.average_uniqueness_weight`,
  `methodology_ml.md` § 6) — to jest ten subtelny wyciek, przed którym
  ostrzega López de Prado rozdz. 4;
- niezmiennik przyczynowości wyższych timeframe'ów trzyma
  (`indicators.asof_index`, `methodology_ml.md` § 3);
- dotknięcie bariery wymaga `volume > 0`, więc minuta `ffill` nie może jej
  wywołać (`labels.triple_barrier`, `methodology_ml.md` § 5);
- `label_valid` nigdy nie bramkuje wejścia — robi to wyłącznie
  `entry_observable` (`methodology_ml.md` § 5). To jest miejsce, w którym
  większość implementacji potrójnej bariery się myli;
- **F2–F4 są in-sample z konstrukcji**: te same foldy wybrały hiperparametry
  (`hpo.build_objective`) i próg τ (`strategy.main`). Czysty jest wyłącznie F5.
  Pytanie audytowe: czy **każdy** odczyt tych liczb — w artefaktach,
  w `<TICKER>_README.md` i na dashboardzie — jest tak oznaczony.

### Determinizm
Wobec `module_skills/skill_determinism.md`, którego standardem dla zmiany bez
skutku jest **parytet bitowy**, nie „wygląda tak samo":

- `SEED`, `nthread=1`, `TPESampler(seed=…)`, `n_jobs=1`, `SET threads=1` na
  połączeniach agregujących;
- połączenia DuckDB w `dataset.write_parquet`, `dataset.load_xy`
  i `strategy.load_inputs` nie ustawiają ani `threads=1`, ani `memory_limit` —
  niespójność dyscypliny czy uzasadniony wyjątek dla odczytów z `ORDER BY`;
- `OMP_NUM_THREADS` ustawia `Makefile` (fan-out) i usługa `asset-btc`, ale
  **nie** usługa `pipeline`, którą biegną `docker-data-*` i `docker-ml-status`;
- Optuna działa w pamięci, bez storage (`hpo.main`) — studium nie jest
  wznawialne ani inspekcyjne po fakcie. Czy `methodology_ml.md` § 7 tego chce.

### Granica odpowiedzialności
`module_ml/bars.py` jest jedynym pisarzem ML w pliku bazy należącym do
`module_data`; każdy inny etap otwiera go `read_only=True`
(`README_module_ml.md` § Where the responsibility stops). Czy nadal jedyny.

## Scope — module_monitoring

- **Reguła nadrzędna działa w dwie strony**
  (`README_module_monitoring.md` § Where the responsibility stops): moduł nigdy
  nie otwiera bazy aktywa i niczego nie przelicza — **oraz** metryka, której nie
  ma w snapshocie, nie ma prawa pojawić się na stronie. Ten drugi kierunek jest
  sprawdzalny: każda wartość renderowana przez `*.js` musi dać się wyprowadzić
  z klucza `data_status.json` albo `ml_status.json`. Wyjątki są nazwane —
  tempo CPU z dwóch próbek (`glossary.md` § Container status endpoint)
  i przerzedzanie osi czasu.
- Jeden serwer, dwie role wybierane obecnością `ASSET`; `record.py` jako jedyny
  właściciel `store_run_records/`.
- **Asymetria walidacji tras — zgodność, nie bezpieczeństwo.** `/runs/<id>`
  i `/containers/<TICKER>/status` sprawdzają przynależność do listy, a
  `/devops/*` przekazuje resztę ścieżki bez sprawdzenia. Pytanie: czy trzy proxy
  jednego modułu mają mieć trzy różne kontrakty wejścia.
- `sub_module_dx/` — czy `visualisation_config.json` jest nadal **całą**
  powierzchnią konfiguracji (`skill_developer_experience_drawing.md`
  § The one rule).
- Czy `sub_module_*` występuje nadal dokładnie dwa razy: konstytucja mówi, że
  dwa to zbieg okoliczności, a trzeci albo bije konwencję, albo żaden
  (`AGENTS.md` § The default choice).

## Scope — sub_module_portraefik

Panel jest opisany w `module_monitoring/skills/skill_devops_panel.md` — jego
widoki, allowlista, guard i socket. **Zlecenie tego nie powtarza**: audytor
czyta skill i weryfikuje kod wobec niego, a nie wobec streszczenia. Poniżej
tylko to, czego w żadnym skillu nie ma, i pytania.

**Trzy fakty spoza dokumentacji:**

1. W `docker-compose.yml` klucz `volumes:` **nadpisuje**, a nie rozszerza
   kotwicę — dlatego bind kodu jest w usłudze `portraefik` powtórzony celowo.
   Usunięcie „duplikatu" odcięłoby panel od `/app`.
2. Koszt jednego odświeżenia panelu w wymianach z demonem: `/api/machines` to
   `2N+1` wymian dla `N` kontenerów na hoście, `/api/networks` to `M+1`;
   pozostałe trasy po jednej–dwie. Wszystkie szeregowo, na świeżym połączeniu.
3. `own_project` i `/api/image` opierają się na tym, że **hostname kontenera
   jest jego identyfikatorem**. Ustawienie `hostname:` w compose cicho zepsułoby
   oba, bez żadnego błędu.

**Pytania:**

- czy allowlist to nadal dokładnie trzy czasowniki i czy nic z listy „nie w v1"
  (`rm`, `exec`, `prune`, operacje na obrazach, compose up/down z przeglądarki,
  streaming logów — `skill_devops_panel.md` § The guard) nie wsiąkło do kodu;
- czy socket jest montowany w jednej usłudze i czy dashboard nadal nie wykonuje
  **żadnego** wywołania Engine (`skill_devops_panel.md` § The one socket…);
- czy panel nadal mówi, **która liczba jest prawdziwsza**: dla aktywa liczby
  z cgroup, nie z Engine (`skill_devops_panel.md` § The views, and which number
  is the truer one);
- `engine_object` i `engine_events` nie łapią `json.JSONDecodeError` — niepełna
  odpowiedź demona kończy się traceback'iem i zerwanym połączeniem bez
  odpowiedzi HTTP, zamiast jednoliniowym komunikatem (`AGENTS.md` § Values);
- każdy udany GET zwraca 200 nawet gdy demon nie odpowiedział; payload jest
  wtedy pusty albo `null`. Czy strona odróżnia „nic nie ma" od „nie wiadomo",
  skoro `skill_devops_panel.md` § What the panel owes the reader każe renderować
  kreski, nigdy poprzednie liczby;
- `act_on_machine` przekazuje kod Engine dosłownie, a docker odpowiada `304` na
  `start` już działającego kontenera; `write_response` i tak dokleja ciało, więc
  powstaje 304 z ciałem, które proxy widzi jako `HTTPError`, a strona renderuje
  jako odmowę — czyli sukces pokazany jako refusal;
- `PanelServer` czyta własny projekt **raz, przy starcie**. Jeśli demon milczał
  w tej sekundzie, panel zostaje read-only i ślepy na zdarzenia do końca życia
  procesu. Fail-closed jest zamierzony — czy trwałość tego stanu też;
- `PANEL_FETCH_TIMEOUT_SECONDS` ogranicza pojedynczą operację gniazda, a nie
  całą wymianę, podczas gdy panel robi `2N+1` wymian szeregowo;
- panel importuje `to_json_bytes` i `write_response` **z modułu dashboardu**.
  Cyklu nie ma, ale dwa procesy dzielą kształt odpowiedzi przez import, a nie
  przez neutralny moduł — czy to mieści się w „sub-moduł ma własny `config.py`
  i własny `main()`" (`AGENTS.md` § The default choice).

## Scope — cross-cutting

- **Siedem guardów jako zamknięta arytmetyka.** `AGENTS.md` § Values wylicza je
  co do jednego. Sprawdzić **obie strony**: czy każdy nazwany guard ma kod,
  i czy każda asercja oraz każdy abort w drzewie mapuje się na nazwany guard.
  **Asercja bez guardu to guard prewencyjny, a guard prewencyjny to contract
  breach.** Uwaga na zamierzoną asymetrię, żeby nie zgłosić jej jako braku:
  sonda listingu istnieje tylko dla Binance, bo listing Bybit wewnątrz okna jest
  dozwolony.
- **Glosariusz jako rejestr dwukierunkowy.** `glossary.md` deklaruje równość
  zbiorów: każdy publikowany klucz jest w rejestrze. Zrzucić klucze
  `data_status.json` i `ml_status.json` i zdiffować z rejestrem. Klucz
  publikowany a nieobecny w glosariuszu to **contract breach**; wiersz
  glosariusza nienazywający żadnego żywego klucza to **drift**.
- **Odrzucone słownictwo — instrukcja, bez której raport będzie szumem.** Lista
  z `AGENTS.md` § Rejected vocabulary **nie ma za sobą żadnego checku** i jest
  tak pomyślana. Wiąże **nazwy w nazwanych warstwach** — segmenty ścieżek,
  stemy modułów i plików, czasowniki funkcji, nazwy kluczy, słowa interfejsu —
  i **nigdy prozy**. Naiwny grep zwraca `service` w kilkunastu plikach i `data`
  w kilkudziesięciu, w komplecie legalnych. Zgodność nazw ocenia się czytaniem,
  nie regexem.
- Reszta listy: gramatyka nazw (`AGENTS.md` § Canonical vocabulary), brak
  znaczników długu i zakomentowanego kodu, ścieżki budowane wyłącznie
  w `config.py` z wyliczonymi wyjątkami, skill żyje w module, którego dotyczy,
  i **dokładnie raz** (`AGENTS.md` § The default choice).

## Calibration

Pięć przykładów. **Trzy z nich nie są znaleziskami** — bo kosztownym błędem
w tym repozytorium jest fałszywy alarm, nie przeoczenie.

**Znalezisko (drift): rysunek DX jest przeterminowany o jeden commit.**
`files_and_folders_visualisation.html` niesie stempel `tree as of 29ffce1`,
podczas gdy HEAD to `c996e41` — a `c996e41` dodał całe `sub_module_portraefik/`,
więc walk-back po commitach „zmieniających tylko stronę" nie może go pominąć.
Strona została przegenerowana z indeksu **wewnątrz** tego commita, więc liczby
węzłów są poprawne, a stempel został o jeden w tyle: **ta sama długość pliku,
inny hash w środku**, dokładnie ta postać, którą
`skill_developer_experience_drawing.md` § The provenance stamp nazywa najgorszą,
jaką może przyjąć zły artefakt. Repozytorium ma na to gotowy check i go nie
uruchamia.

**Znalezisko (drift): nagłówek `run.js` wskazuje na złego właściciela.**
Przypisuje `buildFrame`, `buildKeyValueBox` i `buildFootnote` do `asset.js`, a
`buildMeter`, formatery i `PILL_HOOKS` do `data.js`. Wszystkie siedem mieszka
w `page.js`; poprawne jest wyłącznie „`buildTable` from ml.js". Skoro cały sens
`page.js` polega na tym, że jest **wspólnym przyborem stron**, komentarz kieruje
czytelnika do złego właściciela.

**Nie-znalezisko: `run_dir` i `run_payload` w `module_monitoring`.** Łapią się na
`run_` z listy zakazanych czasowników. Ale `run` jest tu **rzeczownikiem**
(zarejestrowany przebieg, `glossary.md` § Run record), a nazwy są odpowiednio
czystym deskryptorem i builderem payloadu. Zgodne z gramatyką.

**Nie-znalezisko: `gain_importance` liczone z boostera final-holdout.** Wygląda
na liczbę wyprowadzoną z zamkniętego folda — ale `glossary.md` rejestruje ją
dokładnie tak, z boosterem dopasowanym na F1–F4, i zakazuje nazwy „gain
boostera walidacyjnego". To atrybucja, nie wejście do selekcji: decyzja
zapisana, nie przeoczona.

**Nie-znalezisko: plik `.duckdb` nie jest bajtowo stabilny.** `ingest` ustawia
`preserve_insertion_order=false`, więc fizyczny układ bazy może się zmieniać
mimo deterministycznych wyników zapytań. Deklaracja parytetu bajtowego
w `glossary.md` dotyczy README aktywa, a nie bazy — zakres jest już postawiony.
