import csv
import json
import re
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

BASE_DIR = Path(__file__).parent.parent
EVAL_DIR = BASE_DIR / "data" / "eval"
TARGETS_DIR = EVAL_DIR / "targets"
PROPOSALS_DIR = EVAL_DIR / "proposals"

TARGETS_DIR.mkdir(parents=True, exist_ok=True)
PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()


def generate_pdf(filename, title, chapters):
    path = TARGETS_DIR / filename
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    art_num = 1
    for cap_title, articles in chapters:
        story.append(Paragraph(cap_title, styles["Heading1"]))
        story.append(Spacer(1, 6))
        for art_title, art_text in articles:
            story.append(Paragraph(f"Artículo {art_num}. {art_title}", styles["Heading2"]))
            for para in art_text.strip().split("\n"):
                if para.strip():
                    story.append(Paragraph(para.strip(), styles["BodyText"]))
            story.append(Spacer(1, 6))
            art_num += 1

    SimpleDocTemplate(str(path), pagesize=A4).build(story)
    print(f"Generated {path}")


# =============================================================================
# SET 1: TRANSPORTE — few matches scenario (8 / 40 proposals expected to match)
# =============================================================================

transporte_title = "Ley de Transporte Público y Movilidad Sostenible"
transporte_chapters = [
    ("Capítulo I: Disposiciones Generales", [
        ("Objeto.", """1. La presente ley tiene por objeto la ordenación, el fomento y la coordinación del transporte público de viajeros en el territorio nacional, así como el impulso de un modelo de movilidad sostenible, accesible y seguro.
2. Asimismo, regula los derechos de las personas usuarias, las obligaciones de los operadores y el régimen de inspección, control y sanciones aplicables al sector.
3. Lo dispuesto en esta ley se entiende sin perjuicio de las competencias atribuidas a las comunidades autónomas y a las entidades locales en materia de transporte y movilidad."""),
        ("Ámbito de aplicación.", """1. Las disposiciones de esta ley son aplicables a los servicios de transporte público regular y discrecional de viajeros, tanto urbanos como interurbanos, prestados en el territorio nacional.
2. Quedan sujetos a esta ley los operadores públicos y privados que presten servicios mediante concesión administrativa, autorización o cualquier otro título habilitante.
3. Los servicios de transporte escolar, sanitario y los puramente turísticos se regirán por su normativa específica, sin perjuicio de las disposiciones de esta ley que les resulten supletoriamente aplicables."""),
        ("Principios rectores.", """1. La política de transporte público y movilidad se regirá por los principios de accesibilidad universal, sostenibilidad ambiental, eficiencia económica, cohesión territorial y participación ciudadana.
2. Las administraciones competentes promoverán la integración modal, la digitalización de los servicios y la mejora continua de la calidad percibida por las personas usuarias.
3. Se fomentará la equidad en el acceso al transporte público, prestando especial atención a colectivos en situación de vulnerabilidad y a las áreas rurales con menor cobertura."""),
    ]),
    ("Capítulo II: Planificación y Financiación", [
        ("Planes de movilidad urbana sostenible.", """1. Las administraciones locales con población superior a 50.000 habitantes deberán aprobar y revisar, al menos cada cinco años, un plan de movilidad urbana sostenible que ordene los desplazamientos en su término municipal.
2. Los planes incluirán un diagnóstico de la situación actual, los objetivos cuantificables a alcanzar y un programa de medidas con su correspondiente estimación presupuestaria.
3. La aprobación del plan exigirá un proceso de información pública y participación ciudadana, así como informe favorable del órgano autonómico competente."""),
        ("Consorcios metropolitanos de transporte.", """1. Se promoverá la creación de consorcios metropolitanos de transporte como entidades de gestión unificada en áreas con flujos significativos de movilidad entre municipios.
2. Los consorcios coordinarán la planificación, la financiación y la prestación conjunta de los servicios, garantizando la integración tarifaria y operativa entre los distintos modos.
3. Su gobernanza incluirá representantes de las administraciones consorciadas y mecanismos de participación de las personas usuarias y los operadores."""),
        ("Financiación del sistema.", """1. El sistema de transporte público se financiará mediante aportaciones de las administraciones públicas competentes, las tarifas abonadas por las personas usuarias y otros ingresos derivados de la actividad.
2. Las administraciones competentes garantizarán una financiación estable y suficiente para la prestación de un servicio de calidad y para la cobertura de las obligaciones de servicio público.
3. Reglamentariamente se establecerán los criterios de reparto y los mecanismos de control de la ejecución presupuestaria de los recursos destinados al sistema."""),
        ("Fondo Estatal de Movilidad Sostenible.", """1. Se crea el Fondo Estatal de Movilidad Sostenible con la finalidad de apoyar a los municipios y consorcios en la mejora del transporte público y en la transición hacia modelos de movilidad de bajas emisiones.
2. El Fondo se nutrirá con dotaciones presupuestarias anuales, transferencias de la Unión Europea y otros recursos que se determinen reglamentariamente.
3. La distribución del Fondo se realizará mediante convocatorias competitivas en las que se valorarán criterios de ambición ambiental, cohesión territorial e impacto en la calidad del servicio."""),
        ("Bonificaciones tarifarias.", """1. Las administraciones competentes establecerán tarifas reducidas obligatorias en favor de personas estudiantes, familias numerosas, personas mayores de 65 años, personas con discapacidad y otros colectivos en situación de vulnerabilidad económica.
2. Los descuentos no podrán ser inferiores al 30% del precio ordinario, salvo que se prevean tarifas más beneficiosas en la normativa autonómica o local.
3. Las administraciones podrán crear bonos tarifarios específicos vinculados al uso intensivo del transporte público, especialmente para los desplazamientos cotidianos al centro de estudios o de trabajo."""),
        ("Tarifas de integración.", """1. Los consorcios metropolitanos y, en su caso, las administraciones competentes deberán establecer un título único integrado que permita combinar diferentes modos de transporte público dentro del área de su ámbito.
2. La estructura tarifaria garantizará que la combinación de modos no resulte económicamente penalizada respecto al uso de un solo modo de transporte.
3. La integración alcanzará, como mínimo, a los servicios urbanos, metropolitanos y de cercanías ferroviarias que operen en el ámbito del consorcio."""),
        ("Revisión de precios.", """1. La revisión anual de las tarifas no podrá superar el incremento del Índice de Precios al Consumo más un punto porcentual, salvo causas excepcionales debidamente justificadas y autorizadas.
2. Las propuestas de revisión deberán acompañarse de un informe económico que analice su impacto sobre la demanda y sobre los colectivos beneficiarios de bonificaciones.
3. Las administraciones competentes publicarán las nuevas tarifas con una antelación mínima de un mes respecto a su entrada en vigor."""),
    ]),
    ("Capítulo III: Flotas e Infraestructuras", [
        ("Renovación de flotas.", """1. Los operadores deberán retirar progresivamente del servicio los vehículos que superen los diez años de antigüedad, conforme al calendario que se establezca reglamentariamente.
2. La renovación priorizará la incorporación de vehículos de bajas o cero emisiones, con criterios de eficiencia energética y reducción de la contaminación acústica.
3. Las administraciones competentes podrán articular líneas de ayuda específicas para apoyar la renovación de flotas en pequeños operadores y zonas rurales."""),
        ("Electrificación de flotas urbanas.", """1. Al menos el 50% de los nuevos autobuses urbanos adquiridos por los operadores en cada ejercicio deberán ser eléctricos, de hidrógeno o de otra tecnología de cero emisiones directas.
2. El porcentaje se incrementará progresivamente conforme al calendario reglamentario, con el objetivo de alcanzar el 100% de los nuevos vehículos antes de 2035.
3. Reglamentariamente se establecerán las excepciones aplicables a las zonas con limitaciones técnicas justificadas y los mecanismos de seguimiento del cumplimiento."""),
        ("Infraestructura de recarga en cocheras.", """1. Las cocheras y centros operativos de los operadores deberán disponer de los puntos de recarga eléctrica o de repostaje de combustibles alternativos suficientes para atender las necesidades de su flota.
2. Las administraciones competentes podrán cofinanciar la adaptación de las instalaciones existentes mediante convocatorias específicas con cargo al Fondo Estatal de Movilidad Sostenible.
3. La planificación de las infraestructuras de recarga atenderá a la previsión de crecimiento de la flota electrificada en los próximos diez años."""),
        ("Estaciones intermodales.", """1. Las capitales de provincia y los municipios con población superior a 75.000 habitantes deberán disponer de una estación intermodal accesible que articule los servicios de autobús con otros modos de transporte público.
2. Las estaciones contarán con espacios de espera climatizados, aseos públicos, sistemas de información en tiempo real y conexiones peatonales y ciclistas seguras con su entorno.
3. La construcción y modernización de estaciones intermodales se considerará prioritaria a efectos de la financiación con cargo al Fondo Estatal de Movilidad Sostenible."""),
        ("Accesibilidad universal.", """1. Toda la flota de transporte público y las infraestructuras asociadas deberán garantizar la accesibilidad universal mediante rampas, plataformas de embarque a nivel, espacios reservados y sistemas de información sonora y visual.
2. Los operadores adaptarán sus vehículos y procedimientos para atender las necesidades específicas de las personas con movilidad reducida, las personas con discapacidad sensorial y las personas con discapacidad cognitiva.
3. El incumplimiento de las obligaciones de accesibilidad constituirá infracción grave conforme al régimen sancionador previsto en esta ley."""),
        ("Carriles bus.", """1. Los municipios con población superior a 50.000 habitantes deberán reservar carriles exclusivos para el transporte público en sus principales corredores de movilidad, conforme a los criterios técnicos que se establezcan reglamentariamente.
2. La planificación de los carriles bus tendrá en cuenta la prioridad semafórica, la disuasión de invasión por otros vehículos y los mecanismos de control automatizado del cumplimiento.
3. Las inversiones en carriles bus se considerarán prioritarias dentro del programa de medidas de los planes de movilidad urbana sostenible."""),
        ("Sistemas de información en tiempo real.", """1. Las paradas principales de transporte público deberán disponer de paneles informativos en tiempo real que indiquen los próximos servicios, sus tiempos previstos y las posibles incidencias del servicio.
2. La información también se ofrecerá a través de aplicaciones digitales accesibles, sin coste para las personas usuarias y con garantías de protección de datos personales.
3. Los operadores publicarán de forma abierta los datos de explotación necesarios para el desarrollo de servicios de información a la persona usuaria por terceros."""),
        ("Aparcamientos disuasorios.", """1. Las administraciones competentes promoverán la construcción de aparcamientos disuasorios gratuitos en las afueras de las áreas urbanas, conectados con líneas de transporte público de alta frecuencia.
2. Los aparcamientos disuasorios contarán con plazas reservadas para vehículos eléctricos y para personas con movilidad reducida, así como con instalaciones para bicicletas.
3. La gratuidad de los aparcamientos podrá condicionarse a la utilización efectiva del transporte público mediante mecanismos de validación que se establezcan reglamentariamente."""),
        ("Vías ciclistas.", """1. La planificación del transporte público integrará conexiones seguras con la red de vías ciclistas, garantizando la continuidad de los itinerarios y la posibilidad de combinación de modos.
2. Las nuevas estaciones intermodales y los principales nodos de transporte público deberán disponer de aparcamientos seguros para bicicletas y, en su caso, puntos de alquiler.
3. Las administraciones competentes coordinarán sus actuaciones en materia de movilidad ciclista con las previstas en los planes de movilidad urbana sostenible."""),
        ("Mantenimiento preventivo.", """1. Los operadores estarán obligados a realizar el mantenimiento preventivo de sus vehículos al menos con periodicidad semestral, conforme a los protocolos del fabricante y a las normas técnicas aplicables.
2. Los registros de mantenimiento estarán a disposición de la inspección de transporte y se conservarán durante un mínimo de cinco años.
3. El incumplimiento reiterado de las obligaciones de mantenimiento podrá dar lugar a la suspensión cautelar de la actividad, sin perjuicio del régimen sancionador aplicable."""),
    ]),
    ("Capítulo IV: Calidad y Derechos del Usuario", [
        ("Carta de derechos del usuario.", """1. Las personas usuarias del transporte público tienen derecho a recibir un servicio puntual, seguro, limpio y accesible, con arreglo a los estándares de calidad fijados en los títulos concesionales o autorizaciones.
2. Los operadores publicarán y mantendrán visible en sus vehículos, estaciones y canales digitales la carta de derechos del usuario y los procedimientos para hacerlos efectivos.
3. La vulneración sistemática de los derechos reconocidos en este artículo podrá dar lugar a la revisión de las condiciones contractuales con el operador."""),
        ("Reclamaciones y hojas de quejas.", """1. Los operadores deberán disponer de hojas de reclamaciones a disposición de las personas usuarias, tanto en formato físico en sus puntos de atención como a través de canales digitales.
2. Las reclamaciones presentadas se responderán de forma motivada en un plazo máximo de treinta días desde su recepción, sin perjuicio de los plazos más breves previstos en otras disposiciones.
3. Las administraciones competentes mantendrán un registro estadístico de reclamaciones que se publicará anualmente y servirá de base para la evaluación de la calidad del servicio."""),
        ("Indemnizaciones por retrasos.", """1. Los retrasos superiores a sesenta minutos en trayectos interurbanos darán derecho a una indemnización equivalente, como mínimo, al 50% del precio del billete cuando la causa sea imputable al operador.
2. En caso de cancelación del servicio, las personas usuarias tendrán derecho a la devolución íntegra del importe del billete y al transporte alternativo gratuito hasta el destino.
3. Reglamentariamente se establecerán los procedimientos para hacer efectivas las indemnizaciones y los supuestos de fuerza mayor que eximen al operador de su pago."""),
        ("Seguridad ciudadana en el transporte.", """1. Los operadores instalarán cámaras de seguridad en estaciones, intercambiadores y vehículos, conforme a la normativa de protección de datos personales y videovigilancia.
2. Las administraciones competentes coordinarán con las fuerzas y cuerpos de seguridad la prevención y la respuesta ante incidentes de seguridad en el transporte público.
3. Los protocolos de actuación incluirán medidas específicas de prevención del acoso, especialmente del acoso por razón de sexo, y mecanismos accesibles de denuncia."""),
        ("Acceso con mascotas.", """1. Se permitirá el acceso al transporte público con mascotas que viajen en transportines homologados o, en el caso de perros guía y de asistencia, sin restricción.
2. Los operadores podrán habilitar horarios o vagones específicos para el transporte de animales de mayor tamaño en condiciones que garanticen la seguridad y la convivencia.
3. La persona acompañante será responsable del comportamiento del animal y de los daños que este pudiera causar durante el viaje."""),
        ("Transporte de bicicletas.", """1. Los servicios de tren y de autobús interurbano habilitarán espacios específicos para el transporte de bicicletas, con la capacidad mínima que se determine reglamentariamente.
2. El transporte de bicicletas se prestará sin coste adicional para la persona usuaria en los servicios de cercanías ferroviarias y en los autobuses urbanos en horarios de baja ocupación.
3. Los operadores publicarán las condiciones específicas aplicables al transporte de bicicletas en cada línea, incluyendo horarios y eventuales restricciones por demanda."""),
        ("Higiene y limpieza.", """1. Los operadores establecerán protocolos estrictos de limpieza y desinfección diaria de la flota y de las estaciones, con especial atención a los puntos de mayor contacto.
2. Los protocolos contemplarán medidas reforzadas en situaciones de emergencia sanitaria declarada por la autoridad competente.
3. La inspección de transporte podrá realizar comprobaciones periódicas del cumplimiento de los estándares de higiene en colaboración con la autoridad sanitaria."""),
        ("Atención al cliente.", """1. Los operadores deberán mantener un servicio de atención telefónica gratuita, así como puntos de información presencial en las principales estaciones y canales digitales accesibles.
2. La atención se prestará en condiciones de accesibilidad para personas con discapacidad sensorial y, en las áreas con cooficialidad lingüística, en las dos lenguas oficiales.
3. Los tiempos medios de espera y los indicadores de resolución de incidencias se publicarán trimestralmente como parte del seguimiento de la calidad del servicio."""),
        ("Auditorías de calidad.", """1. Los títulos concesionales y las autorizaciones incluirán la realización de encuestas anuales de satisfacción de las personas usuarias, cuyos resultados serán vinculantes para la evaluación del servicio.
2. Las encuestas serán realizadas por entidades independientes designadas por la administración competente, con metodología homologada y muestra estadísticamente representativa.
3. Los resultados se publicarán en un plazo máximo de tres meses desde la finalización del trabajo de campo y se incorporarán al expediente de seguimiento de la concesión."""),
        ("Sanciones a operadores por incumplimiento.", """1. El incumplimiento reiterado de los horarios establecidos será considerado como falta grave del operador, sin perjuicio de las indemnizaciones que pudieran corresponder a las personas usuarias.
2. La graduación de la sanción atenderá al porcentaje de servicios afectados, a la duración del incumplimiento y a la afectación sobre los itinerarios prioritarios.
3. La reincidencia en faltas graves podrá dar lugar a la revisión de las condiciones contractuales o, en su caso, a la revocación del título habilitante."""),
    ]),
    ("Capítulo V: Régimen Sancionador", [
        ("Inspección de transporte.", """1. La inspección de transporte velará por el cumplimiento de las obligaciones establecidas en esta ley, en su normativa de desarrollo y en los títulos concesionales o autorizaciones.
2. El personal inspector tendrá carácter de agente de la autoridad y podrá acceder a las instalaciones, vehículos y documentación de los operadores en el ejercicio de sus funciones.
3. Las administraciones competentes dispondrán de los medios humanos y materiales necesarios para garantizar una inspección eficaz y proporcionada."""),
        ("Faltas leves.", """1. Se consideran faltas leves los retrasos menores no justificados, las deficiencias puntuales en la información a las personas usuarias y los incumplimientos formales de las obligaciones documentales.
2. Asimismo tendrá la consideración de falta leve el incumplimiento aislado de los protocolos de limpieza ordinaria, siempre que no afecte a la seguridad o salud de las personas usuarias.
3. Las faltas leves prescribirán al año desde la fecha de su comisión."""),
        ("Faltas graves.", """1. Tendrán la consideración de faltas graves la operación de vehículos sin las condiciones de accesibilidad legalmente exigibles, los incumplimientos reiterados de horarios y la prestación de servicios con vehículos sin el mantenimiento preventivo en regla.
2. Asimismo se calificarán como graves las conductas que pongan en riesgo la seguridad de las personas usuarias, siempre que no constituyan falta muy grave.
3. Las faltas graves prescribirán a los dos años desde la fecha de su comisión."""),
        ("Faltas muy graves.", """1. Constituyen faltas muy graves la prestación de servicios sin el oportuno título concesional, autorización o seguro obligatorio, así como las conductas que generen daños graves a las personas usuarias o a terceros.
2. Tendrá igualmente la consideración de muy grave la manipulación dolosa de los registros de mantenimiento o de los datos relativos a la prestación del servicio.
3. Las faltas muy graves prescribirán a los tres años desde la fecha de su comisión."""),
        ("Cuantía de las sanciones.", """1. Las multas por faltas leves oscilarán entre 100 y 1.000 euros; las correspondientes a faltas graves, entre 1.001 y 10.000 euros; y las correspondientes a faltas muy graves, entre 10.001 y 50.000 euros.
2. La graduación de la sanción atenderá a la gravedad del hecho, al perjuicio causado, al beneficio obtenido y a la reincidencia.
3. Las cuantías podrán actualizarse anualmente conforme al Índice de Precios al Consumo mediante orden ministerial."""),
        ("Fraude por parte de las personas usuarias.", """1. Viajar sin título de transporte válido conllevará un recargo de 50 euros que deberá abonarse en el momento de su requerimiento por el personal de inspección.
2. La negativa a abonar el recargo, así como el uso fraudulento reiterado del transporte público, podrá dar lugar a la imposición de sanciones conforme al régimen general previsto en esta ley.
3. Las administraciones competentes desarrollarán campañas de información para concienciar sobre las consecuencias del fraude y promover el uso responsable del transporte público."""),
        ("Reincidencia.", """1. La acumulación de tres faltas graves o de una falta muy grave en el plazo de doce meses podrá motivar la revocación del título concesional o de la autorización del operador.
2. Reglamentariamente se determinarán los criterios de cómputo de la reincidencia y los procedimientos aplicables a la revocación.
3. La revocación se acordará previa audiencia del operador y mediante resolución motivada de la administración competente."""),
        ("Destino de las multas.", """1. La recaudación obtenida por las multas impuestas en aplicación de esta ley se destinará íntegramente a la mejora del sistema de transporte público y a la financiación del Fondo Estatal de Movilidad Sostenible.
2. La administración correspondiente publicará anualmente un informe sobre el importe recaudado y los proyectos financiados con cargo a estos recursos.
3. La afectación finalista de la recaudación no impedirá la aplicación de los criterios generales de gestión presupuestaria."""),
        ("Prescripción de las infracciones.", """1. Las infracciones tipificadas en esta ley prescriben al año, a los dos años o a los tres años, según se trate de faltas leves, graves o muy graves, respectivamente.
2. El plazo de prescripción se interrumpe con la incoación del procedimiento sancionador y se reanuda si este permanece paralizado por causa no imputable al presunto responsable.
3. Las sanciones impuestas prescribirán a los plazos previstos en la legislación general sobre procedimiento administrativo."""),
        ("Medidas cautelares.", """1. La inspección de transporte podrá inmovilizar vehículos cuando exista riesgo grave e inminente para la seguridad de las personas usuarias o cuando se preste el servicio sin el oportuno título habilitante.
2. La adopción de medidas cautelares deberá ratificarse por la autoridad competente en el plazo máximo de cuarenta y ocho horas.
3. La inmovilización podrá levantarse cuando se acredite la subsanación de las circunstancias que motivaron su adopción."""),
    ]),
]


# Matches (8 of 40) — same gold mapping as before
transporte_proposals = []
transporte_expected = []

transporte_proposals.append(("transporte-1", "Deberían hacer descuentos obligatorios para los jóvenes que estudian, porque el bono normal es muy caro y la gente se busca la vida en el coche."))
transporte_expected.append(("Artículo 8. Bonificaciones tarifarias.", ["transporte-1"]))

transporte_proposals.append(("transporte-2", "Es urgente que todos los autobuses tengan rampa, no podemos dejar a la gente en silla de ruedas tirada en la parada esperando que llegue un bus accesible."))
transporte_expected.append(("Artículo 15. Accesibilidad universal.", ["transporte-2"]))

transporte_proposals.append(("transporte-3", "Hay que obligar a que los autobuses urbanos nuevos sean eléctricos para no contaminar el centro de las ciudades, especialmente en zonas con problemas de calidad del aire."))
transporte_expected.append(("Artículo 12. Electrificación de flotas urbanas.", ["transporte-3"]))

transporte_proposals.append(("transporte-4", "Estaría muy bien que pusieran pantallas en las paradas para saber cuánto falta para que llegue el bus, así no estás esperando sin saber si va a tardar diez minutos o cuarenta."))
transporte_expected.append(("Artículo 17. Sistemas de información en tiempo real.", ["transporte-4"]))

transporte_proposals.append(("transporte-5", "Debería haber un solo billete para combinar el tren, el metro y el bus de toda el área metropolitana, sin tener que pagar otra vez al cambiar de medio."))
transporte_expected.append(("Artículo 9. Tarifas de integración.", ["transporte-5"]))

transporte_proposals.append(("transporte-6", "Si el tren de cercanías llega tarde más de una hora por culpa de la operadora, deberían devolverte el dinero del billete o parte de él."))
transporte_expected.append(("Artículo 23. Indemnizaciones por retrasos.", ["transporte-6"]))

transporte_proposals.append(("transporte-7", "Hay que permitir subir la bicicleta al tren o al bus interurbano para combinar los dos medios de transporte sin tener que llevarla desmontada."))
transporte_expected.append(("Artículo 26. Transporte de bicicletas.", ["transporte-7"]))

transporte_proposals.append(("transporte-8", "Si te pillan sin billete, la multa que te pongan debería ir directamente a comprar mejores autobuses y no perderse en la caja general."))
transporte_expected.append(("Artículo 38. Destino de las multas.", ["transporte-8"]))


# Non-matches (32 of 40) — realistic citizen proposals that touch transport-adjacent
# topics but are NOT regulated by any article of this law.
transporte_non_matches = [
    "Tendrían que poner controles de alcohol y drogas obligatorios y aleatorios a los conductores de bus al inicio del turno, igual que se hace con los pilotos de avión.",
    "Hay que crear una línea de bus nocturno que vaya cada 30 minutos hasta las 4 de la madrugada en las zonas de marcha, para que la gente no tenga que volver en coche bebida.",
    "Los conductores de autobús deberían cobrar más, su sueldo es muy bajo para la responsabilidad de llevar a cien personas en hora punta y aguantar el tráfico.",
    "Habría que regular las patinetes eléctricos compartidos en las ciudades, que están tirados por todas partes y a veces alguien se cae por culpa de uno mal aparcado.",
    "Hace falta una ley que regule los Uber, Cabify y similares para que jueguen con las mismas reglas que los taxis tradicionales.",
    "El transporte escolar tendría que ser gratuito para todos los niños que vivan a más de tres kilómetros del colegio, no solo para los de zonas rurales.",
    "Tendrían que regular los aviones para que no salgan de los aeropuertos cercanos a las ciudades antes de las siete de la mañana, hay barrios que no descansan.",
    "Habría que limitar los cruceros que llegan a las ciudades portuarias, descargan miles de turistas en un día y se cargan los barrios.",
    "Deberían crear un carnet de conducir específico para personas mayores de 70 años con revisiones obligatorias cada dos años.",
    "Es indignante que los taxistas se nieguen a llevarte si pagas con tarjeta, debería estar prohibido por ley aceptar solo efectivo.",
    "Hay que poner radares fijos en todas las salidas de los colegios para multar a los coches que pasen a más de 20 km/h en horario escolar.",
    "Tendría que existir un seguro obligatorio para bicicletas y patinetes eléctricos, igual que para los coches, por si atropellas a alguien.",
    "El autoescuela debería ser gratuita para personas en paro de larga duración, sacarse el carnet cuesta dos mil euros y sin coche es difícil encontrar trabajo.",
    "Hace falta una ley que prohíba aparcar coches en las aceras, los peatones tienen que bajarse a la calzada y los carritos de bebé no pasan.",
    "Habría que poner peajes en las entradas de las grandes ciudades para los coches privados, el dinero podría ir a financiar el transporte público.",
    "Tendrían que regular el ruido de las motos modificadas, hay quien se compra un escape ilegal y va por el barrio a las dos de la mañana.",
    "Deberían poner radares de tramo en todas las autopistas y autovías nacionales, no solo en algunas, para evitar accidentes mortales.",
    "Hay que crear una tarifa plana mensual para todo el transporte estatal, incluido AVE, igual que existe para el transporte regional.",
    "Tendrían que devolver el carril bici a Madrid Río que quitaron, era un sitio seguro para que aprendieran los niños y ahora no hay donde ir.",
    "Habría que prohibir los motores de explosión en los coches de alquiler turístico de las islas, son lugares pequeños y no tiene sentido contaminar.",
    "El gobierno tendría que subvencionar la compra de coches eléctricos para particulares, los precios son inalcanzables para una familia normal.",
    "Hace falta una normativa que obligue a los polígonos industriales a tener servicio de bus lanzadera para los trabajadores, hay sitios sin transporte público.",
    "Tendrían que limitar los vuelos cortos peninsulares cuando exista alternativa en tren de menos de tres horas, como han hecho en Francia.",
    "Habría que regular los días de huelga del transporte público fijando servicios mínimos del 70% para que la gente pueda ir a trabajar.",
    "Es urgente reformar el examen teórico del carnet de conducir, las preguntas están desactualizadas y no incluyen movilidad eléctrica ni patinetes.",
    "Tendría que ser obligatorio que los coches eléctricos hicieran ruido a baja velocidad, los ciegos no los oyen llegar y es peligroso en los pasos de cebra.",
    "Hay que modernizar las estaciones de tren rurales, muchas están abandonadas y dan miedo de noche, especialmente para mujeres viajando solas.",
    "Habría que crear ayudas específicas para los autónomos del taxi que tienen que renovar coche cada cinco o seis años por las exigencias de la ZBE.",
    "Deberían existir cursos obligatorios de conducción para mayores cada cinco años después de los 65, con simuladores de reacciones lentas.",
    "Tendría que ser obligatorio el chaleco reflectante para ciclistas urbanos en horario nocturno, igual que para los conductores que se bajan del coche.",
    "Hay que regular el uso de drones de reparto en las ciudades, antes de que cualquier empresa empiece a tirar paquetes desde el aire sin control.",
    "Habría que estudiar la viabilidad de un tren de alta velocidad transversal que conecte directamente las capitales de provincia sin pasar por Madrid.",
]
for i, text in enumerate(transporte_non_matches, start=9):
    transporte_proposals.append((f"transporte-{i}", text))

# Multi-match additions: extra proposals for high-interest articles
transporte_proposals.append(("transporte-41", "Los pensionistas tendrían que pagar mucho menos en el autobús, muchos cobran una pensión mínima y no se pueden permitir el billete ordinario."))
transporte_expected.append(("Artículo 8. Bonificaciones tarifarias.", ["transporte-41"]))

transporte_proposals.append(("transporte-42", "Las familias numerosas con varios hijos deberían pagar menos en el transporte público, porque si viajan tres o cuatro personas el gasto mensual es desorbitado."))
transporte_expected.append(("Artículo 8. Bonificaciones tarifarias.", ["transporte-42"]))

transporte_proposals.append(("transporte-43", "Las personas ciegas o con discapacidad visual necesitan que el bus anuncie las paradas en voz alta, si no tienen que contar paradas y muchas veces se pasan."))
transporte_expected.append(("Artículo 15. Accesibilidad universal.", ["transporte-43"]))

transporte_proposals.append(("transporte-44", "La calidad del aire en los barrios con mucho tráfico de autobuses es horrible, hay que obligar a que todos los autobuses nuevos sean eléctricos y no solo un porcentaje."))
transporte_expected.append(("Artículo 12. Electrificación de flotas urbanas.", ["transporte-44"]))

# Extra non-matches (transport-adjacent topics not regulated by this law)
transporte_non_matches_extra = [
    "Deberían limitar las mallas publicitarias que cubren los autobuses enteros por fuera, porque tapan las ventanas y los viajeros no ven nada desde dentro.",
    "Habría que regular los servicios de autobús turístico de dos pisos descubiertos en los centros históricos, van demasiado rápido y hacen mucho ruido.",
    "Tendría que ser obligatorio que los taxistas hablen un nivel mínimo de español para poder comunicarse con los viajeros, especialmente en zonas turísticas.",
    "Hay que crear un registro público de operadoras de VTC para que cualquier ciudadano pueda comprobar si el coche que ha pedido tiene los papeles en regla.",
    "Deberían multar más a los coches que aparcan en doble fila bloqueando el carril bus, es un problema gravísimo en las ciudades y los agentes hacen la vista gorda.",
    "Habría que crear una aplicación oficial del gobierno para pagar el parking en todas las ciudades, ahora hay diez aplicaciones distintas y ninguna funciona igual.",
    "Es un escándalo que los peajes de autopistas ya amortizadas sigan siendo de pago, habría que eliminarlos y destinar ese tráfico a las vías libres de peaje.",
    "Tendría que existir una ley que obligue a los usuarios de patinetes de alquiler a llevar casco, igual que los que van en bicicleta convencional.",
    "Habría que regular los cruceros en los puertos urbanos que descargan miles de personas en pocas horas y colapsan el transporte local de toda la ciudad.",
    "Deberían prohibir a los camiones que crucen el centro histórico de las ciudades en horario diurno, ahora mismo contaminan y destrozan el pavimento.",
    "Hay que regular los drones de reparto comercial en zonas urbanas antes de que las empresas empiecen a lanzarlos sobre los barrios sin ningún control.",
    "Tendría que existir un límite de velocidad diferenciado para las motos en ciudad, van mucho más rápido que los coches y el riesgo de atropello es alto.",
    "Habría que crear ayudas para que los autónomos del sector del taxi puedan jubilarse a una edad razonable, es un trabajo muy duro y no pueden aguantar hasta los 70.",
    "Hace falta una normativa clara sobre quién es responsable cuando un vehículo autónomo causa un accidente, ahora mismo no hay legislación específica al respecto.",
    "Deberían regular las empresas de mudanzas para que no puedan bloquear la calle entera con su camión durante horas sin pedir permiso al ayuntamiento.",
    "Habría que obligar a que todos los nuevos edificios residenciales incluyan aparcamiento de bicis cubierto y seguro en planta baja, no solo plazas de coche.",
]
for i, text in enumerate(transporte_non_matches_extra, start=45):
    transporte_proposals.append((f"transporte-{i}", text))


# =============================================================================
# SET 2: CLIMA — many matches scenario (22 / 40 proposals expected to match)
# =============================================================================

clima_title = "Ley de Cambio Climático y Transición Energética"
clima_chapters = [
    ("Capítulo I: Disposiciones Generales", [
        ("Objeto.", """1. La presente ley tiene por objeto asegurar el cumplimiento de los objetivos del Acuerdo de París, promoviendo la transición ordenada hacia un modelo socioeconómico neutro en carbono y resiliente frente a los efectos del cambio climático.
2. La ley regula los instrumentos de planificación, los objetivos cuantitativos de reducción de emisiones, las medidas sectoriales aplicables y los mecanismos de gobernanza climática.
3. Las disposiciones de esta ley se aplicarán en todo el territorio nacional, sin perjuicio de las competencias autonómicas y locales en materia de medio ambiente y energía."""),
        ("Principios rectores.", """1. La política climática se rige por los principios de desarrollo sostenible, descarbonización progresiva, justicia climática, no regresión ambiental y participación ciudadana.
2. Los principios de cautela, prevención y «quien contamina paga» orientarán las decisiones públicas en materia de cambio climático y de transición energética.
3. Las administraciones públicas garantizarán la coherencia de sus políticas sectoriales con los objetivos climáticos establecidos en esta ley."""),
        ("Objetivos de reducción de emisiones.", """1. Se establece como objetivo nacional la reducción de las emisiones de gases de efecto invernadero en al menos un 50% para el año 2030 respecto a los niveles de 1990.
2. El objetivo de neutralidad climática se alcanzará no más tarde del año 2050 mediante una senda de reducción que se concretará en los planes nacionales integrados de energía y clima.
3. La revisión periódica de los objetivos atenderá a las evidencias científicas más recientes y a los compromisos internacionales asumidos por el Reino de España."""),
    ]),
    ("Capítulo II: Energías Renovables", [
        ("Fomento de las energías renovables.", """1. El sistema eléctrico nacional deberá alcanzar al menos un 70% de generación a partir de fuentes de energía renovable en el año 2030, conforme a la senda establecida en el plan nacional integrado de energía y clima.
2. Se priorizarán las tecnologías con menor impacto ambiental y territorial, así como las que ofrezcan mayores beneficios para las comunidades locales en las que se ubiquen.
3. Las administraciones competentes simplificarán los procedimientos administrativos para la autorización de instalaciones de generación renovable, sin menoscabo de la protección ambiental."""),
        ("Autoconsumo eléctrico.", """1. Se simplificarán los trámites administrativos para la instalación de paneles solares para autoconsumo doméstico, comunitario e industrial, eliminando barreras burocráticas innecesarias.
2. Las personas y entidades titulares de instalaciones de autoconsumo tendrán derecho a la compensación por los excedentes vertidos a la red en los términos que se establezcan reglamentariamente.
3. Las administraciones competentes desarrollarán líneas de ayuda específicas para apoyar a los hogares con menor capacidad económica en el acceso al autoconsumo."""),
        ("Comunidades energéticas locales.", """1. Se fomentará la creación de comunidades energéticas locales como entidades sin ánimo de lucro orientadas a producir, consumir, almacenar y compartir energía renovable en su entorno próximo.
2. Las administraciones competentes establecerán mecanismos específicos de apoyo técnico y financiero a la constitución y desarrollo de comunidades energéticas, con prioridad para las áreas rurales y los barrios vulnerables.
3. La participación de las administraciones locales en las comunidades energéticas no podrá superar el 30% de los derechos de voto, salvo en supuestos excepcionales debidamente justificados."""),
        ("Energía eólica.", """1. Las administraciones competentes elaborarán y publicarán mapas de zonificación que identifiquen áreas idóneas y áreas de exclusión para la instalación de parques eólicos terrestres y marinos.
2. Los criterios de zonificación atenderán al recurso eólico disponible, a la afección sobre la biodiversidad, al patrimonio cultural y paisajístico y a las preferencias manifestadas en los procesos de participación.
3. La autorización de nuevos parques eólicos en áreas de exclusión solo será posible mediante procedimiento extraordinario debidamente motivado."""),
        ("Modernización de las redes de distribución.", """1. La red de distribución eléctrica se modernizará para integrar de forma eficiente la generación distribuida, el autoconsumo y los puntos de recarga de vehículos eléctricos.
2. Los planes de inversión de las empresas distribuidoras incluirán las actuaciones necesarias para garantizar la digitalización, la flexibilidad y la resiliencia de la red.
3. Reglamentariamente se establecerán los mecanismos de seguimiento y control del cumplimiento de los planes de inversión por parte del organismo regulador."""),
        ("Almacenamiento energético.", """1. Se impulsarán proyectos de almacenamiento energético a gran escala mediante baterías electroquímicas, bombeo hidroeléctrico y otras tecnologías equivalentes.
2. Las administraciones competentes podrán establecer mecanismos de retribución específicos para los servicios prestados al sistema por las instalaciones de almacenamiento.
3. La planificación del almacenamiento atenderá a su contribución a la integración de energías renovables variables y a la garantía de suministro."""),
        ("Cierre del carbón y planificación.", """1. Se prohíbe la apertura de nuevas centrales térmicas de generación eléctrica que utilicen carbón como combustible principal a partir de la entrada en vigor de esta ley.
2. Se planifica el cierre ordenado de las centrales térmicas de carbón existentes antes del año 2030, con planes específicos de transición justa para las comarcas afectadas.
3. La administración competente coordinará el calendario de cierre con las medidas de garantía de suministro y con la creación de empleo alternativo en las regiones implicadas."""),
    ]),
    ("Capítulo III: Movilidad y Eficiencia Energética", [
        ("Zonas de Bajas Emisiones.", """1. Los municipios con población superior a 50.000 habitantes y los territorios insulares deberán establecer Zonas de Bajas Emisiones antes del año 2028, conforme a las directrices que se establezcan reglamentariamente.
2. Las Zonas de Bajas Emisiones contemplarán restricciones progresivas a la circulación de los vehículos más contaminantes, atendiendo a su clasificación ambiental.
3. Los municipios garantizarán la disponibilidad de alternativas de transporte público y de movilidad activa para los desplazamientos afectados por las restricciones."""),
        ("Venta de vehículos de combustión.", """1. No se permitirá la venta de turismos y vehículos comerciales ligeros nuevos con motores de combustión interna a partir del año 2040, sin perjuicio del calendario más exigente que pueda derivarse de la normativa europea.
2. Las administraciones competentes acompañarán la transición con líneas de ayuda específicas para la adquisición de vehículos eléctricos por hogares con menor capacidad económica.
3. El cierre progresivo de la matriculación de vehículos de combustión no afectará al uso, mantenimiento ni venta de los vehículos ya matriculados."""),
        ("Puntos de recarga en gasolineras.", """1. Las gasolineras con ventas anuales superiores a cinco millones de litros deberán instalar al menos un punto de recarga eléctrica de potencia equivalente a la de uso normal del vehículo eléctrico.
2. Reglamentariamente se establecerá el calendario de cumplimiento, las potencias mínimas exigibles y las características técnicas que deberán reunir los puntos de recarga.
3. El incumplimiento de la obligación impedirá la renovación de las licencias administrativas de la instalación, sin perjuicio del régimen sancionador aplicable."""),
        ("Flota pública.", """1. La administración pública deberá renovar su flota de vehículos optando exclusivamente por modelos eléctricos, de hidrógeno u otras tecnologías de cero emisiones directas.
2. La obligación se aplicará a las nuevas adquisiciones a partir de la entrada en vigor de esta ley, conforme al calendario que se establezca para cada categoría de vehículo.
3. Quedan exceptuados los vehículos para los que no exista en el mercado una alternativa de cero emisiones que satisfaga los requisitos técnicos del servicio público correspondiente."""),
        ("Rehabilitación energética de edificios.", """1. Se establecen líneas de ayuda directa para la mejora del aislamiento térmico, la sustitución de ventanas y la modernización de los sistemas de climatización en viviendas construidas con anterioridad al año 2006.
2. Las ayudas se modularán en función de la renta del hogar, del grado de mejora alcanzado y de la situación de pobreza energética acreditada.
3. Las administraciones competentes garantizarán la asistencia técnica gratuita a las personas solicitantes durante la tramitación de las ayudas."""),
        ("Certificado energético en compraventa y alquiler.", """1. Será obligatorio disponer de un certificado de eficiencia energética con calificación C o superior para la venta o el alquiler de viviendas a partir del año 2030.
2. Se exceptuarán de la obligación los inmuebles protegidos por la legislación de patrimonio histórico, sin perjuicio de la obligación de informar a la persona adquirente o arrendataria.
3. El incumplimiento de la obligación podrá ser sancionado conforme a lo previsto en la normativa específica de eficiencia energética en edificios."""),
        ("Edificios públicos y autoconsumo.", """1. Todos los edificios de titularidad pública deberán instalar paneles solares en sus cubiertas siempre que sea técnicamente viable y compatible con la protección del patrimonio histórico.
2. La planificación de las instalaciones se incorporará a los planes anuales de inversión y se publicará en formato accesible para la ciudadanía.
3. Las administraciones titulares destinarán los excedentes de generación a abastecer otros equipamientos públicos o, en su defecto, a la compensación de excedentes."""),
        ("Alumbrado público eficiente.", """1. Los ayuntamientos deberán sustituir el 100% de su alumbrado público por tecnología LED de bajo consumo antes del año 2030.
2. La sustitución se acompañará de la implantación de sistemas de regulación inteligente que permitan ajustar la intensidad lumínica a las necesidades reales de cada zona.
3. Las administraciones autonómicas establecerán líneas de cofinanciación específicas para apoyar a los municipios de menor población en el cumplimiento de esta obligación."""),
        ("Transporte de mercancías.", """1. Se incentivará el traslado del transporte de mercancías de la carretera al ferrocarril mediante bonificaciones fiscales, ayudas a la modalidad y planificación de las infraestructuras intermodales.
2. Los corredores ferroviarios prioritarios para el transporte de mercancías se identificarán en el plan estratégico estatal de logística sostenible.
3. Las administraciones competentes coordinarán las medidas con los puertos de interés general para garantizar la continuidad de las cadenas logísticas."""),
        ("Movilidad compartida.", """1. Se fomentarán los sistemas de coche compartido, bicicleta compartida y otras formas de movilidad colaborativa en los entornos metropolitanos y en los polos de actividad económica.
2. Los planes de movilidad urbana sostenible incluirán medidas específicas de impulso de la movilidad compartida y de su integración con el transporte público.
3. Las administraciones competentes podrán reservar espacio público para los servicios de movilidad compartida que cumplan estándares ambientales y de inclusión."""),
    ]),
    ("Capítulo IV: Adaptación y Biodiversidad", [
        ("Planes de adaptación al cambio climático.", """1. Todas las comunidades autónomas deberán aprobar planes de adaptación al cambio climático que evalúen las vulnerabilidades de su territorio frente a olas de calor, sequías, inundaciones y otros riesgos climáticos.
2. Los planes incluirán objetivos cuantificables, medidas con su correspondiente dotación presupuestaria y mecanismos de seguimiento basados en indicadores comunes.
3. La revisión de los planes se realizará al menos cada cinco años o ante cambios significativos en la información científica disponible."""),
        ("Zonas verdes urbanas.", """1. Los planes urbanísticos deberán garantizar un mínimo de 15 metros cuadrados de zona verde por habitante en los nuevos desarrollos urbanos y en los procesos de transformación urbana.
2. Las zonas verdes incorporarán especies autóctonas y de bajo consumo hídrico, así como soluciones basadas en la naturaleza para la gestión del agua de lluvia.
3. Las administraciones competentes elaborarán inventarios públicos del arbolado urbano y planes de protección frente a episodios de calor extremo."""),
        ("Reforestación y sumideros de carbono.", """1. Se crea un fondo forestal estatal destinado a replantar áreas afectadas por incendios y a crear grandes sumideros de carbono naturales en el territorio nacional.
2. Las actuaciones priorizarán la diversidad de especies autóctonas, la prevención de incendios mediante la gestión activa del monte y la compatibilidad con los usos tradicionales del territorio.
3. La administración competente publicará anualmente un informe sobre la superficie reforestada, los costes asociados y la captura estimada de carbono."""),
        ("Gestión del agua y regadíos.", """1. Se prohíben las nuevas concesiones de regadío intensivo en cuencas hidrográficas declaradas en estrés hídrico severo por la autoridad competente.
2. Las concesiones existentes en dichas cuencas se revisarán con criterios de eficiencia, prioridad social del recurso y compatibilidad con los caudales ecológicos.
3. Se promoverán inversiones en modernización de regadíos, reutilización de aguas regeneradas y mejora de la eficiencia de las redes de distribución."""),
        ("Protección de costas frente a la subida del nivel del mar.", """1. Se limitará la construcción de nuevas edificaciones en zonas litorales identificadas como vulnerables a la subida del nivel del mar conforme a los escenarios climáticos oficiales.
2. La administración competente delimitará periódicamente las zonas vulnerables y establecerá las restricciones aplicables a los usos del suelo en cada una de ellas.
3. Las administraciones autonómicas y locales adaptarán su planeamiento territorial y urbanístico a las restricciones derivadas de la protección costera."""),
        ("Agricultura ecológica y regenerativa.", """1. Se subvencionará la transición hacia modelos de agricultura ecológica y regenerativa que retengan carbono en el suelo y reduzcan las emisiones asociadas a la actividad agraria.
2. Las ayudas estarán condicionadas al cumplimiento de prácticas verificables que mejoren la fertilidad natural del suelo, la biodiversidad y la eficiencia hídrica.
3. Las administraciones competentes coordinarán las ayudas con las previstas en la política agraria común para evitar duplicidades y garantizar la complementariedad."""),
        ("Sistemas de alerta temprana.", """1. Se implementará un sistema nacional de alerta temprana ante fenómenos meteorológicos extremos vinculados al cambio climático, accesible para la ciudadanía y los servicios de emergencia.
2. El sistema integrará la información de las redes de observación, los modelos de predicción y los protocolos de actuación de los servicios de protección civil.
3. La administración competente garantizará la difusión inmediata de las alertas en formatos accesibles para personas con discapacidad sensorial."""),
        ("Refugios climáticos en municipios.", """1. Los ayuntamientos deberán habilitar refugios climáticos en bibliotecas, centros cívicos y otros equipamientos públicos para la población durante las olas de calor estivales.
2. Los refugios contarán con climatización suficiente, accesibilidad universal, acceso a agua potable y horarios ampliados durante los episodios de calor extremo.
3. Las administraciones autonómicas apoyarán a los municipios de menor población mediante líneas de cofinanciación específicas para la habilitación de refugios."""),
        ("Restauración de humedales y turberas.", """1. Se declaran prioritarios los proyectos de restauración de humedales y turberas degradadas como elementos clave para la captura de carbono y la regulación hídrica.
2. La administración competente identificará el inventario nacional de humedales degradados susceptibles de restauración y elaborará un plan plurianual de actuaciones.
3. Las actuaciones se realizarán con criterios de participación de las comunidades locales y de compatibilidad con los usos sostenibles del territorio."""),
        ("Biodiversidad marina.", """1. Se ampliarán las áreas marinas protegidas hasta alcanzar el 30% de la superficie marítima nacional antes del año 2030, conforme a los compromisos internacionales asumidos.
2. Los planes de gestión de las áreas marinas protegidas incluirán medidas específicas frente al calentamiento del mar, la acidificación y la pérdida de hábitats.
3. Las administraciones competentes coordinarán las actuaciones con los Estados ribereños mediante los acuerdos regionales aplicables al espacio marino correspondiente."""),
    ]),
    ("Capítulo V: Transición Justa y Gobernanza", [
        ("Convenios de transición justa.", """1. Se firmarán convenios de transición justa con las regiones afectadas por el cierre de centrales térmicas, las cuencas mineras y otros sectores sometidos a una transformación intensa por la política climática.
2. Los convenios incluirán medidas de empleo, formación, reactivación económica e infraestructuras, con dotación presupuestaria plurianual y mecanismos de gobernanza participativa.
3. La administración competente publicará informes anuales de seguimiento de los convenios con indicadores de empleo, inversión y satisfacción de las comunidades afectadas."""),
        ("Fiscalidad verde.", """1. Se reformará el sistema fiscal para gravar las actividades más contaminantes y bonificar las prácticas sostenibles, en coherencia con los objetivos de la presente ley.
2. Los ingresos derivados de la fiscalidad ambiental se afectarán prioritariamente a la financiación de la transición justa y de las medidas de adaptación al cambio climático.
3. La reforma incorporará mecanismos para mitigar los efectos regresivos de la fiscalidad ambiental sobre los hogares con menor capacidad económica."""),
        ("Educación ambiental.", """1. El currículo escolar básico deberá incluir la educación ambiental y la crisis climática de forma transversal en todas las etapas educativas obligatorias.
2. Las administraciones educativas garantizarán la formación específica del profesorado y la disponibilidad de materiales didácticos actualizados sobre estas materias.
3. Se promoverá la colaboración con las administraciones medioambientales para el desarrollo de programas educativos en espacios naturales y de divulgación científica."""),
        ("Comité Científico de Cambio Climático.", """1. Se crea el Comité Científico de Cambio Climático como órgano independiente encargado de evaluar las políticas públicas en materia climática y de emitir recomendaciones a las autoridades competentes.
2. Sus integrantes serán designados con criterios de mérito científico, paridad de género y diversidad disciplinar, y ejercerán sus funciones con plena independencia.
3. Los informes del Comité tendrán carácter público y serán remitidos al gobierno y al parlamento para su consideración en los procesos legislativos."""),
        ("Presupuestos con perspectiva climática.", """1. Al menos el 25% de los presupuestos generales del Estado se destinará a políticas con impacto positivo frente al cambio climático, conforme a una metodología homologada de etiquetado climático.
2. La memoria presupuestaria incluirá un informe específico que justifique el cumplimiento del porcentaje exigido y describa los principales programas financiados.
3. La metodología de etiquetado se revisará periódicamente para incorporar las mejores prácticas internacionales y los avances científicos disponibles."""),
        ("Inversiones financieras y riesgos climáticos.", """1. Las grandes empresas y las instituciones financieras deberán publicar un informe anual sobre los riesgos climáticos asociados a sus carteras de activos y sobre las estrategias de mitigación adoptadas.
2. El informe se ajustará a las directrices internacionales reconocidas y será objeto de verificación independiente conforme a los estándares aplicables.
3. La autoridad supervisora establecerá los criterios de seguimiento del cumplimiento y podrá requerir información adicional cuando lo considere necesario."""),
        ("Asambleas ciudadanas por el clima.", """1. Se convocarán periódicamente asambleas ciudadanas por el clima para debatir medidas y formular propuestas que serán objeto de tramitación parlamentaria con carácter vinculante.
2. La selección de las personas participantes se realizará por sorteo cualificado para garantizar la representatividad demográfica, territorial y social de la población.
3. Las asambleas dispondrán del apoyo técnico independiente necesario para deliberar sobre la base de la mejor información científica disponible."""),
        ("Huella de carbono empresarial.", """1. Las medianas y grandes empresas deberán calcular y registrar anualmente su huella de carbono conforme a una metodología homologada por la administración competente.
2. El registro de huella de carbono será público en sus aspectos esenciales, sin perjuicio de la protección de la información comercialmente sensible.
3. La administración competente promoverá programas voluntarios de compensación de emisiones vinculados al registro de huella de carbono."""),
        ("Compras públicas sostenibles.", """1. Las licitaciones públicas incluirán cláusulas que primen a las empresas con menores emisiones a lo largo del ciclo de vida de los bienes y servicios contratados.
2. Reglamentariamente se establecerán criterios técnicos homologados que permitan la valoración objetiva de las ofertas en función de su desempeño climático.
3. Las administraciones publicarán anualmente indicadores agregados sobre la contribución climática de su contratación pública."""),
        ("Seguimiento parlamentario.", """1. El gobierno presentará anualmente al parlamento un informe de seguimiento de la aplicación de esta ley, con indicadores cuantitativos sobre el cumplimiento de los objetivos.
2. El informe será objeto de debate específico en pleno y se acompañará de las recomendaciones formuladas por el Comité Científico de Cambio Climático.
3. La administración competente publicará el informe y la información de base en formatos abiertos y accesibles para la ciudadanía."""),
    ]),
]


# Matches (22 of 40) — same gold mapping as before
clima_proposals = []
clima_expected = []

clima_proposals.append(("clima-1", "La crisis climática es el mayor reto de nuestra época y la ley debe asegurar de una vez por todas que cumplimos lo pactado en el Acuerdo de París."))
clima_expected.append(("Artículo 1. Objeto.", ["clima-1"]))

clima_proposals.append(("clima-2", "Hay que quitar tanta burocracia para poner paneles solares en el tejado de tu casa, que ahora mismo son meses de papeles y permisos absurdos."))
clima_expected.append(("Artículo 5. Autoconsumo eléctrico.", ["clima-2"]))

clima_proposals.append(("clima-3", "Las ciudades grandes (las de más de cincuenta mil habitantes) tienen que restringir los coches contaminantes para tener zonas de bajas emisiones de verdad."))
clima_expected.append(("Artículo 11. Zonas de Bajas Emisiones.", ["clima-3"]))

clima_proposals.append(("clima-4", "Deberían dar dinero para mejorar el aislamiento térmico de los pisos viejos, que se escapa todo el calor en invierno y en verano se cocina la gente."))
clima_expected.append(("Artículo 15. Rehabilitación energética de edificios.", ["clima-4"]))

clima_proposals.append(("clima-5", "Hay que enseñar ecología y crisis climática a los niños en el colegio, en todas las asignaturas posibles, no solo en una optativa."))
clima_expected.append(("Artículo 33. Educación ambiental.", ["clima-5"]))

clima_proposals.append(("clima-6", "Los ayuntamientos deberían cambiar todas las bombillas de las farolas por luces LED para ahorrar energía y reducir la factura."))
clima_expected.append(("Artículo 18. Alumbrado público eficiente.", ["clima-6"]))

clima_proposals.append(("clima-7", "En verano hace muchísimo calor, los ayuntamientos tienen que abrir sitios frescos como bibliotecas para que la gente sin aire acondicionado se refugie."))
clima_expected.append(("Artículo 28. Refugios climáticos en municipios.", ["clima-7"]))

clima_proposals.append(("clima-8", "Hay que prohibir ya las centrales de carbón, contaminan muchísimo y no deberíamos abrir ninguna más en este país."))
clima_expected.append(("Artículo 10. Cierre del carbón y planificación.", ["clima-8"]))

clima_proposals.append(("clima-9", "La administración pública tiene que dar ejemplo y comprar solo coches eléctricos para sus flotas, no puede pedir lo que no hace."))
clima_expected.append(("Artículo 14. Flota pública.", ["clima-9"]))

clima_proposals.append(("clima-10", "Se debería poner un impuesto a las cosas que más contaminan y quitar impuestos a lo verde, para que la gente vea claro lo que conviene."))
clima_expected.append(("Artículo 32. Fiscalidad verde.", ["clima-10"]))

clima_proposals.append(("clima-11", "Tendrían que poner puntos de recarga para coches eléctricos en las gasolineras grandes, que son las que más venden y tienen sitio."))
clima_expected.append(("Artículo 13. Puntos de recarga en gasolineras.", ["clima-11"]))

clima_proposals.append(("clima-12", "Estaría bien que los vecinos del barrio pudieran juntarse para crear una comunidad y compartir la energía de los paneles solares del bloque."))
clima_expected.append(("Artículo 6. Comunidades energéticas locales.", ["clima-12"]))

clima_proposals.append(("clima-13", "La ley tiene que dejar claro desde el principio que no vamos a dar pasos atrás en protección ambiental, que sea irreversible."))
clima_expected.append(("Artículo 2. Principios rectores.", ["clima-13"]))

clima_proposals.append(("clima-14", "Necesitamos mapas claros para saber dónde se pueden poner molinos de viento sin dañar pueblos ni naturaleza, y dónde no."))
clima_expected.append(("Artículo 7. Energía eólica.", ["clima-14"]))

clima_proposals.append(("clima-15", "Hay que crear un fondo para plantar más árboles en zonas que se han quemado, no se puede dejar el monte así durante años."))
clima_expected.append(("Artículo 23. Reforestación y sumideros de carbono.", ["clima-15"]))

clima_proposals.append(("clima-16", "No podemos dar más permisos para regar donde ya casi no hay agua, hay que parar los regadíos intensivos en cuencas con sequía severa."))
clima_expected.append(("Artículo 24. Gestión del agua y regadíos.", ["clima-16"]))

clima_proposals.append(("clima-17", "Los grandes bancos y empresas tienen que publicar obligatoriamente qué riesgos tienen sus inversiones frente al cambio climático."))
clima_expected.append(("Artículo 36. Inversiones financieras y riesgos climáticos.", ["clima-17"]))

clima_proposals.append(("clima-18", "Las empresas tendrían que calcular cuánta huella de carbono dejan cada año e inscribirla en un registro público."))
clima_expected.append(("Artículo 38. Huella de carbono empresarial.", ["clima-18"]))

clima_proposals.append(("clima-19", "Hay que organizar asambleas de ciudadanos normales, elegidos por sorteo, para que debatan sobre el clima y sus propuestas se voten en el parlamento."))
clima_expected.append(("Artículo 37. Asambleas ciudadanas por el clima.", ["clima-19"]))

clima_proposals.append(("clima-20", "Cuando cierren las minas o centrales térmicas, hay que firmar acuerdos de transición para no dejar a los trabajadores tirados ni a sus pueblos."))
clima_expected.append(("Artículo 31. Convenios de transición justa.", ["clima-20"]))

clima_proposals.append(("clima-21", "Hay que proteger las turberas y humedales degradados porque absorben mucho carbono y los hemos descuidado durante décadas."))
clima_expected.append(("Artículo 29. Restauración de humedales y turberas.", ["clima-21"]))

clima_proposals.append(("clima-22", "Debería haber más zonas verdes en las ciudades, un mínimo de metros cuadrados por habitante para que se respire mejor en verano."))
clima_expected.append(("Artículo 22. Zonas verdes urbanas.", ["clima-22"]))


# Non-matches (18 of 40) — realistic citizen proposals on environmental or
# adjacent topics that this law does NOT specifically regulate.
clima_non_matches = [
    "Habría que prohibir los plásticos de un solo uso en los bares y restaurantes, no tiene sentido seguir tirando pajitas y vasos a la basura cada día.",
    "Es indignante la cantidad de comida que tiran los supermercados al cierre, debería estar prohibido y obligatorio donarla a bancos de alimentos.",
    "Hay que regular el desperdicio textil de las grandes marcas, queman ropa nueva sin usar y eso es un escándalo medioambiental enorme.",
    "Tendría que estar prohibido vender botellas de agua de un solo uso en las administraciones públicas, deberían tener fuentes filtradas.",
    "Habría que poner un impuesto al mar a las navieras de mercancías que pasan cerca de la costa, contaminan muchísimo el aire de los puertos.",
    "Deberían regular el ruido de los aviones por la noche, hay zonas cerca del aeropuerto donde no se puede dormir entre las dos y las cinco.",
    "Hace falta una ley que limite la pirotecnia en fiestas patronales, los animales de compañía sufren ataques y los pájaros mueren de estrés.",
    "Tendría que ser obligatorio recoger las cacas de perro con bolsas biodegradables, las normales tardan siglos en deshacerse en el suelo.",
    "Habría que prohibir los anuncios publicitarios de productos contaminantes en televisión, igual que se hizo con el tabaco en su momento.",
    "Hay que regular la pesca de arrastre cerca de la costa, está destrozando los fondos marinos y vaciando los caladeros tradicionales.",
    "Deberían poner cámaras térmicas obligatorias en los vertederos para detectar incendios antes de que se descontrolen, ahora se enteran tarde.",
    "Tendría que existir una etiqueta clara de bienestar animal en los productos cárnicos del supermercado, ahora no sabes lo que compras.",
    "Habría que regular las terrazas de bares en invierno con estufas de gas al aire libre, es un absurdo calentar la calle a propósito.",
    "Las grandes superficies tendrían que recoger los electrodomésticos viejos cuando entregan los nuevos, para que la gente no acabe abandonándolos.",
    "Es necesario regular la cría intensiva de cerdos en macrogranjas, contaminan los acuíferos y los pueblos pequeños no pueden con esto.",
    "Habría que prohibir las tarimas con calefactores en las terrazas de los chiringuitos en zonas protegidas de la costa, son una aberración.",
    "Tendría que existir un servicio de recogida gratuito de aceite de cocina usado en los barrios, ahora la gente lo tira por el fregadero.",
    "Hace falta una ley que regule la luz artificial nocturna en zonas rurales para proteger la fauna y devolver el cielo estrellado a la gente.",
]
for i, text in enumerate(clima_non_matches, start=23):
    clima_proposals.append((f"clima-{i}", text))

# Multi-match additions: extra proposals for high-interest articles
clima_proposals.append(("clima-41", "Mi comunidad de vecinos quiere poner paneles en el tejado del bloque y repartir la electricidad generada entre todos los pisos, pero los trámites son una pesadilla burocrática."))
clima_expected.append(("Artículo 5. Autoconsumo eléctrico.", ["clima-41"]))

clima_proposals.append(("clima-42", "Si se pudiera vender la electricidad sobrante de los paneles solares a la red eléctrica, muchos más vecinos se animarían a instalarlos en sus casas."))
clima_expected.append(("Artículo 5. Autoconsumo eléctrico.", ["clima-42"]))

clima_proposals.append(("clima-43", "Los locales comerciales pequeños también deberían poder instalar paneles en el tejado sin tener que contratar a un ingeniero y pagar cuatro informes técnicos distintos."))
clima_expected.append(("Artículo 5. Autoconsumo eléctrico.", ["clima-43"]))

clima_proposals.append(("clima-44", "Las zonas de bajas emisiones están bien, pero hay que vigilar que se cumplan de verdad y que los coches viejos no sigan circulando con pegatinas falsificadas."))
clima_expected.append(("Artículo 11. Zonas de Bajas Emisiones.", ["clima-44"]))

clima_proposals.append(("clima-45", "Las ZBE no pueden aplicarse igual para todos, la gente que no se puede permitir un coche eléctrico necesita un periodo de adaptación largo y ayudas económicas reales."))
clima_expected.append(("Artículo 11. Zonas de Bajas Emisiones.", ["clima-45"]))

clima_proposals.append(("clima-46", "No tiene ningún sentido restringir los coches si luego no hay transporte público bueno que los sustituya, las ZBE tienen que ir acompañadas de más autobuses y metros."))
clima_expected.append(("Artículo 11. Zonas de Bajas Emisiones.", ["clima-46"]))

clima_proposals.append(("clima-47", "Los edificios de los años 60 y 70 son un colador térmico, hay que subvencionar el aislamiento de fachadas para que los vecinos puedan pagarlo sin endeudarse."))
clima_expected.append(("Artículo 15. Rehabilitación energética de edificios.", ["clima-47"]))

clima_proposals.append(("clima-48", "Muchos propietarios no rehabilitan su piso porque no tienen el dinero por adelantado aunque luego ahorren en calefacción, hace falta financiación sin intereses o con periodos de carencia."))
clima_expected.append(("Artículo 15. Rehabilitación energética de edificios.", ["clima-48"]))

clima_proposals.append(("clima-49", "Hay que plantar muchos más árboles en las aceras de las ciudades, en verano la diferencia de temperatura entre una calle con sombra y una sin árboles es de varios grados."))
clima_expected.append(("Artículo 22. Zonas verdes urbanas.", ["clima-49"]))

clima_proposals.append(("clima-50", "Los nuevos barrios se construyen sin ni un árbol ni un parque real, hay que exigir que los promotores incluyan zonas verdes de verdad y no solo un césped decorativo."))
clima_expected.append(("Artículo 22. Zonas verdes urbanas.", ["clima-50"]))

clima_proposals.append(("clima-51", "Los niños aprenden mucho más sobre la naturaleza si la tocan y la cuidan, los colegios deberían tener un huerto escolar en el patio para trabajar el medio ambiente de forma práctica."))
clima_expected.append(("Artículo 33. Educación ambiental.", ["clima-51"]))

# Extra non-matches (environmental-adjacent topics not regulated by this law)
clima_non_matches_extra = [
    "Habría que prohibir la venta de fuegos artificiales al público general, los incendios forestales en verano muchas veces empiezan por una bengala mal apagada.",
    "Hay que regular las granjas acuícolas en el litoral, están contaminando las playas con sus vertidos y destruyendo los ecosistemas marinos costeros.",
    "Tendría que existir una etiqueta de sostenibilidad obligatoria en la ropa para saber cuánta agua y energía se usó para fabricarla, como el nutriscore pero para el textil.",
    "Es un escándalo que las empresas de mensajería usen furgonetas sin criterio por las ciudades, habría que regular las zonas y franjas horarias de reparto urbano.",
    "Habría que exigir a los supermercados que informen del origen del producto en el etiquetado, para que el consumidor pueda elegir lo local y reducir emisiones de transporte.",
    "Hace falta una ley que regule la publicidad de vuelos baratos, que incentivan viajes innecesarios y no reflejan el coste real en emisiones de carbono.",
    "Tendría que prohibirse la apertura de nuevas canteras en zonas de alta biodiversidad aunque tengan todos los papeles, porque el daño al paisaje es irreparable.",
    "Habría que crear una tasa específica sobre los envases de plástico de bebidas para financiar los costes de recogida y reciclaje que paga toda la sociedad.",
    "Deberían regular la obsolescencia programada de los electrodomésticos, que el fabricante obligue a dar repuestos y asistencia técnica durante al menos diez años.",
]
for i, text in enumerate(clima_non_matches_extra, start=52):
    clima_proposals.append((f"clima-{i}", text))


def consolidate_expected(expected_list):
    """Merge multiple entries for the same article into one."""
    merged = {}
    order = []
    for article, refs in expected_list:
        if article not in merged:
            merged[article] = []
            order.append(article)
        merged[article].extend(refs)
    return [(art, merged[art]) for art in order]


_ARTICLE_NUM = re.compile(r"Artículo\s+(\d+)")


def _sort_expected(expected_list):
    """Sort expected entries by article number; non-numeric titles sort last."""
    def key(item):
        m = _ARTICLE_NUM.search(item[0])
        return int(m.group(1)) if m else float("inf")
    return sorted(expected_list, key=key)


# =============================================================================
# WRITE OUTPUTS
# =============================================================================

def write_csv(filename, proposals):
    path = PROPOSALS_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "reference", "text"])
        for i, (ref, text) in enumerate(proposals):
            writer.writerow([i + 1, ref, text])
    print(f"Generated {path}")


generate_pdf("PILOTO2_Transporte.pdf", transporte_title, transporte_chapters)
generate_pdf("PILOTO2_Clima.pdf", clima_title, clima_chapters)

write_csv("transporte.csv", transporte_proposals)
write_csv("clima.csv", clima_proposals)

# Update testset.json (replace any existing transporte/clima entries)
testset_path = EVAL_DIR / "testset.json"
with open(testset_path, "r", encoding="utf-8") as f:
    data = json.load(f)

cases = [c for c in data.get("cases", []) if c["domain"] not in ("transporte", "clima")]

cases.append({
    "domain": "transporte",
    "target": "targets/PILOTO2_Transporte.pdf",
    "proposals": "proposals/transporte.csv",
    "expected": [{"article": art, "proposal_refs": refs}
                 for art, refs in _sort_expected(consolidate_expected(transporte_expected))],
})

cases.append({
    "domain": "clima",
    "target": "targets/PILOTO2_Clima.pdf",
    "proposals": "proposals/clima.csv",
    "expected": [{"article": art, "proposal_refs": refs}
                 for art, refs in _sort_expected(consolidate_expected(clima_expected))],
})

data["cases"] = cases

with open(testset_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"Updated {testset_path}")
