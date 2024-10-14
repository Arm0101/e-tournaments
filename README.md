# e-tournaments

## Autores

    -Armando Padrón
    -Abdel Fregel Hernández

## Tema

E-tournaments

## Torneos en-lı́nea

En la actualidad existen muchos juegos de dos jugadores con implementaciones computacionales.
De igual manera que entre humanos, es habitual que se organicen torneos donde los protagonistas
son los jugadores virtuales. En ocasiones los jugadores virtuales, ası́ como la lógica propia de los
juegos, necesitan de un elevado poder de cómputo. Por este motivo la implementación de un torneo,
de efectuarse en un único equipo de cómputo, requerirı́a de un equipo de buen rendimiento y podrı́a
conllevar una larga duración. Debido a que los enfrentamientos entre dos jugadores virtuales en un
juego determinado no tiene relación con otro enfrentamiento entre dos jugadores del propio torneo
entonces los enfrentamientos virtuales se pueden desarrollar en varias computadoras a la vez.

## Especificaciones

El proyecto que se propone tiene como propósito implementar un sistema distribuido que permita la
organización de torneos de un juego determinado donde se pueda utilizar la capacidad de cómputo
de varios equipos. El sistema debe permitir definir desde un cliente especı́fico los jugadores
virtuales y el tipo de torneo a efectuar ası́ como la consulta y visualización de todos los resultados y
estadı́sticas del torneo. Igualmente debe preveer de un mecanismo de tolerancia a fallas de forma
que el desarrollo del torneo no sea interrumpido por el fallo de un equipo donde se estén efectuando
un conjunto de enfrentamientos. De la misma forma debe preveer que se puedan desarrollar varios
torneos a la vez.

## Recomendaciones

El sistema que se proponga debe poseer las sisguientes cararecterísticas:

- Arquitectura distribuida.
- Tolerancia a fallas.
- Migración de código de los jugadores virtuales al nodo donde se efectúen los enfrentamientos.
- Capacidad para definir varias modalidades de torneos (todos contra todos, eliminación directa, por
grupos...etc)
- Acceso desde el cliente a la información del desarrollo del torneo y las estadísticas del mismo.
- Capacidad para desarrollar varios torneos simultáneamente.

> Nota
Cualquier enriquecimiento del proyecto es válido y se tendrá en cuenta en la evaluación del mismo.
En caso de modificar la orden del proyecto debe consultarse a los profesores con anterioridad
