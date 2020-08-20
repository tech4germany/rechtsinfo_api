from unittest import mock

from rip_api.ingest.gesetze_im_internet import LawXmlParser, Law, Article, Heading, HeadingArticle


@mock.patch('rip_api.ingest.gesetze_im_internet.glob', return_value=['mock.xml'])
def test_parser_e2e(glob_mock):
    mock_open = mock.mock_open(read_data=XML_DATA)
    with mock.patch('rip_api.ingest.gesetze_im_internet.open', mock_open):
        parsed = LawXmlParser('mock/xml/dir/path', 'mylaw').parse()

    assert parsed.dict() == EXPECTED_LAW.dict()


XML_DATA = """\
<?xml version="1.0" encoding="UTF-8" ?><!DOCTYPE dokumente SYSTEM "http://www.gesetze-im-internet.de/dtd/1.01/gii-norm.dtd">
<dokumente builddate="20200722212521" doknr="BJNR055429995"><norm builddate="20200722212521" doknr="BJNR055429995"><metadaten><jurabk>SkAufG</jurabk><amtabk>SkAufG</amtabk><ausfertigung-datum manuell="ja">1995-07-20</ausfertigung-datum><fundstelle typ="amtlich"><periodikum>BGBl II</periodikum><zitstelle>1995, 554</zitstelle></fundstelle><kurzue>Streitkräfteaufenthaltsgesetz</kurzue><langue>Gesetz über die Rechtsstellung ausländischer Streitkräfte bei
vorübergehenden Aufenthalten in der Bundesrepublik Deutschland</langue><standangabe checked="ja"><standtyp>Stand</standtyp><standkommentar>Zuletzt geändert durch Art. 191 V v. 19.6.2020 I 1328</standkommentar></standangabe></metadaten><textdaten><fussnoten><Content><P><BR/> <pre xml:space="preserve">(+++ Textnachweis ab: 27.7.1995 +++)<BR/><BR/></pre></P></Content></fussnoten></textdaten></norm>
<norm builddate="20200722212521" doknr="BJNR055429995BJNE000600305"><metadaten><jurabk>SkAufG</jurabk><gliederungseinheit><gliederungskennzahl>000</gliederungskennzahl><gliederungsbez>-</gliederungsbez></gliederungseinheit><enbez>Eingangsformel</enbez></metadaten><textdaten><text format="XML"><Content><P>Der Bundestag hat mit Zustimmung des Bundesrates das folgende Gesetz beschlossen:</P></Content></text></textdaten></norm>
<norm builddate="20200722212521" doknr="BJNR055429995BJNG000100305"><metadaten><jurabk>SkAufG</jurabk><gliederungseinheit><gliederungskennzahl>010</gliederungskennzahl><gliederungsbez>Art 1</gliederungsbez></gliederungseinheit></metadaten><textdaten><text format="XML"><Content><P>(1) Die Bundesregierung wird ermächtigt, Vereinbarungen mit ausländischen Staaten über Einreise und vorübergehenden Aufenthalt ihrer Streitkräfte in der Bundesrepublik Deutschland für Übungen, Durchreise auf dem Landwege und Ausbildung von Einheiten durch Rechtsverordnung ohne Zustimmung des Bundesrates in Kraft zu setzen.</P><P>(2) Vereinbarungen dürfen nur mit solchen Staaten geschlossen werden, die auch der Bundeswehr den Aufenthalt in ihrem Hoheitsgebiet gestatten.</P><P>(3) Die betroffenen Länder werden beteiligt.</P></Content>  </text></textdaten></norm>
<norm builddate="20200722212521" doknr="BJNR055429995BJNG000200305"><metadaten><jurabk>SkAufG</jurabk><gliederungseinheit><gliederungskennzahl>020</gliederungskennzahl><gliederungsbez>Art 2</gliederungsbez></gliederungseinheit></metadaten><textdaten><text format="XML"><Content><P>In die Vereinbarungen werden, soweit nach ihrem Gegenstand und Zweck erforderlich, Regelungen mit folgendem Inhalt aufgenommen.</P></Content></text></textdaten></norm>
<norm builddate="20200722212521" doknr="BJNR055429995BJNE000700305"><metadaten><jurabk>SkAufG</jurabk><gliederungseinheit><gliederungskennzahl>020</gliederungskennzahl><gliederungsbez>Art 2</gliederungsbez></gliederungseinheit><enbez>§ 1</enbez><titel format="parat">Allgemeine Voraussetzungen</titel></metadaten><textdaten><text format="XML"><Content><P>(1) Für Einreise und Aufenthalt bestimmen sich die Rechte und Pflichten der ausländischen Streitkräfte und ihrer Mitglieder nach den deutschen Gesetzen und Rechtsvorschriften.</P><P>(2) In der Vereinbarung sind die Rahmenbedingungen für den Aufenthalt der ausländischen Streitkräfte nach Art, Umfang und Dauer festzulegen.</P></Content> </text></textdaten></norm>
<norm builddate="20200722212521" doknr="BJNR055429995BJNE000801310"><metadaten><jurabk>SkAufG</jurabk><gliederungseinheit><gliederungskennzahl>020</gliederungskennzahl><gliederungsbez>Art 2</gliederungsbez></gliederungseinheit><enbez>§ 2</enbez><titel format="parat">Grenzübertritt, Einreise</titel></metadaten><textdaten><text format="XML"><Content><P>(1) Ausländische Streitkräfte und deren Mitglieder sind im Rahmen dieses Gesetzes und der ausländerrechtlichen Vorschriften berechtigt, mit Land-, Wasser- und Luftfahrzeugen in die Bundesrepublik Deutschland einzureisen und sich in oder über dem Bundesgebiet aufzuhalten.</P><P>(2) Mitglieder ausländischer Streitkräfte, die zum militärischen Personal gehören, müssen beim Grenzübertritt mit sich führen entweder <DL Font="normal" Type="arabic"><DT>a)</DT><DD Font="normal"><LA Size="normal">einen gültigen Paß oder ein anerkanntes Paßersatzpapier oder</LA></DD> <DT>b)</DT><DD Font="normal"><LA Size="normal">einen amtlichen Lichtbildausweis, sofern sie in eine Sammelliste eingetragen sind und sich der Einheits- oder Verbandsführer durch einen gültigen Paß oder ein anerkanntes Paßersatzpapier ausweisen kann.</LA></DD> </DL> </P><P>(3) Mitglieder ausländischer Streitkräfte, die zum zivilen Personal gehören, müssen beim Grenzübertritt einen gültigen Paß oder ein anerkanntes Paßersatzpapier mit sich führen.</P><P>(4) Mitglieder ausländischer Streitkräfte weisen sich durch einen Paß, ein anerkanntes Paßersatzpapier oder, soweit sie zum militärischen Personal gehören, durch eine Sammelliste in Verbindung mit einem amtlichen Lichtbildausweis aus.</P><P>(5) Es gelten die internationalen und die deutschen Gesundheitsvorschriften. Bei der Einreise in die Bundesrepublik Deutschland kann die Vorlage eines von den Behörden des ausländischen Staates ausgestellten amtlichen Gesundheitszeugnisses verlangt werden, aus dem hervorgeht, daß die Mitglieder ausländischer Streitkräfte frei von ansteckenden Krankheiten sind.</P><P>(6) Wird die öffentliche Sicherheit oder Ordnung der Bundesrepublik Deutschland durch ein ziviles oder militärisches Mitglied einer ausländischen Streitkraft gefährdet, so kann die Bundesrepublik Deutschland die unverzügliche Entfernung des Mitgliedes durch die ausländischen Streitkräfte verlangen. In der Vereinbarung ist zu bestimmen, daß die Behörden des Entsendestaates solchen Entfernungsersuchen nachzukommen und die Aufnahme des betreffenden Mitgliedes im eigenen Hoheitsgebiet zu gewährleisten haben. Im übrigen bleiben die Bestimmungen des Aufenthaltsgesetzes unberührt.</P></Content>    </text><fussnoten/></textdaten></norm>
<norm builddate="20200722212521" doknr="BJNR055429995BJNG000300305"><metadaten><jurabk>SkAufG</jurabk><gliederungseinheit><gliederungskennzahl>030</gliederungskennzahl><gliederungsbez>Art 3</gliederungsbez></gliederungseinheit></metadaten><textdaten><text format="XML"><Content><P/></Content></text></textdaten></norm>
<norm builddate="20200722212521" doknr="BJNR055429995BJNE002801311"><metadaten><jurabk>SkAufG</jurabk><gliederungseinheit><gliederungskennzahl>030</gliederungskennzahl><gliederungsbez>Art 3</gliederungsbez><gliederungstitel/></gliederungseinheit><enbez>§ 1</enbez></metadaten><textdaten><text format="XML"><Content><P>Das Bundesministerium der Verteidigung erläßt im Einvernehmen mit dem Bundesministerium des Innern, für Bau und Heimat allgemeine Verwaltungsvorschriften zur Ausführung des Artikels 2 § 5 über Besitz und Führen von Schußwaffen der diesem Gesetz unterfallenden ausländischen Militärangehörigen.</P></Content></text><fussnoten/></textdaten></norm>
<norm builddate="20200722212521" doknr="BJNR055429995BJNE002900305"><metadaten><jurabk>SkAufG</jurabk><gliederungseinheit><gliederungskennzahl>030</gliederungskennzahl><gliederungsbez>Art 3</gliederungsbez></gliederungseinheit><enbez>§ 2</enbez></metadaten><textdaten><text format="XML"><Content><P>Der Verzicht auf die Ausübung der deutschen Gerichtsbarkeit gemäß Artikel 2 § 7 Abs. 2 wird von der Staatsanwaltschaft erklärt.</P></Content></text></textdaten></norm>
<norm builddate="20200722212521" doknr="BJNR055429995BJNG000400305"><metadaten><jurabk>SkAufG</jurabk><gliederungseinheit><gliederungskennzahl>040</gliederungskennzahl><gliederungsbez>Art 4</gliederungsbez></gliederungseinheit></metadaten><textdaten><text format="XML"><Content><P>Dieses Gesetz findet keine Anwendung auf <ABWFORMAT typ="A"/>Militärattaches eines ausländischen Staates in der Bundesrepublik Deutschland, die Mitglieder ihrer Stäbe sowie andere Militärpersonen, die in der Bundesrepublik Deutschland einen diplomatischen oder konsularischen Status haben.</P></Content></text></textdaten></norm>
</dokumente>"""

EXPECTED_LAW = Law(
    id='BJNR055429995',
    juris_abbrs=['SkAufG'],
    official_abbr='SkAufG',
    first_published='1995-07-20',
    source_timestamp='20200722212521',
    heading_long='Gesetz über die Rechtsstellung ausländischer Streitkräfte bei\nvorübergehenden Aufenthalten in der Bundesrepublik Deutschland',
    heading_short='Streitkräfteaufenthaltsgesetz',
    publication_info=[{'periodical': 'BGBl II', 'reference': '1995, 554'}],
    status_info=[{'category': 'Stand', 'comment': 'Zuletzt geändert durch Art. 191 V v. 19.6.2020 I 1328'}],
    prelude={'body': None, 'footnotes': '<P><BR/> <pre xml:space="preserve">(+++ Textnachweis ab: 27.7.1995 +++)<BR/><BR/></pre></P>'},
    content=[
        Article(
            id='BJNR055429995BJNE000600305',
            name='Eingangsformel',
            title=None,
            body={'content': '<P>Der Bundestag hat mit Zustimmung des Bundesrates das folgende Gesetz beschlossen:</P>', 'toc': None, 'footnotes': None},
            footnotes=None
        ),
        Article(
            id='BJNR055429995BJNG000100305',
            name='Art 1',
            title=None,
            body={'content': '<P>(1) Die Bundesregierung wird ermächtigt, Vereinbarungen mit ausländischen Staaten über Einreise und vorübergehenden Aufenthalt ihrer Streitkräfte in der Bundesrepublik Deutschland für Übungen, Durchreise auf dem Landwege und Ausbildung von Einheiten durch Rechtsverordnung ohne Zustimmung des Bundesrates in Kraft zu setzen.</P><P>(2) Vereinbarungen dürfen nur mit solchen Staaten geschlossen werden, die auch der Bundeswehr den Aufenthalt in ihrem Hoheitsgebiet gestatten.</P><P>(3) Die betroffenen Länder werden beteiligt.</P>', 'toc': None, 'footnotes': None},
            footnotes=None
        ),
        HeadingArticle(
            id='BJNR055429995BJNG000200305',
            name='Art 2',
            title=None,
            body={'content': '<P>In die Vereinbarungen werden, soweit nach ihrem Gegenstand und Zweck erforderlich, Regelungen mit folgendem Inhalt aufgenommen.</P>', 'toc': None, 'footnotes': None},
            footnotes=None,
            heading_level=0,
            children=[
                Article(
                    id='BJNR055429995BJNE000700305',
                    name='§ 1',
                    title='Allgemeine Voraussetzungen',
                    body={'content': '<P>(1) Für Einreise und Aufenthalt bestimmen sich die Rechte und Pflichten der ausländischen Streitkräfte und ihrer Mitglieder nach den deutschen Gesetzen und Rechtsvorschriften.</P><P>(2) In der Vereinbarung sind die Rahmenbedingungen für den Aufenthalt der ausländischen Streitkräfte nach Art, Umfang und Dauer festzulegen.</P>', 'toc': None, 'footnotes': None},
                    footnotes=None
                ),
                Article(
                    id='BJNR055429995BJNE000801310',
                    name='§ 2',
                    title='Grenzübertritt, Einreise',
                    body={'content': '<P>(1) Ausländische Streitkräfte und deren Mitglieder sind im Rahmen dieses Gesetzes und der ausländerrechtlichen Vorschriften berechtigt, mit Land-, Wasser- und Luftfahrzeugen in die Bundesrepublik Deutschland einzureisen und sich in oder über dem Bundesgebiet aufzuhalten.</P><P>(2) Mitglieder ausländischer Streitkräfte, die zum militärischen Personal gehören, müssen beim Grenzübertritt mit sich führen entweder <DL Font="normal" Type="arabic"><DT>a)</DT><DD Font="normal"><LA Size="normal">einen gültigen Paß oder ein anerkanntes Paßersatzpapier oder</LA></DD> <DT>b)</DT><DD Font="normal"><LA Size="normal">einen amtlichen Lichtbildausweis, sofern sie in eine Sammelliste eingetragen sind und sich der Einheits- oder Verbandsführer durch einen gültigen Paß oder ein anerkanntes Paßersatzpapier ausweisen kann.</LA></DD> </DL> </P><P>(3) Mitglieder ausländischer Streitkräfte, die zum zivilen Personal gehören, müssen beim Grenzübertritt einen gültigen Paß oder ein anerkanntes Paßersatzpapier mit sich führen.</P><P>(4) Mitglieder ausländischer Streitkräfte weisen sich durch einen Paß, ein anerkanntes Paßersatzpapier oder, soweit sie zum militärischen Personal gehören, durch eine Sammelliste in Verbindung mit einem amtlichen Lichtbildausweis aus.</P><P>(5) Es gelten die internationalen und die deutschen Gesundheitsvorschriften. Bei der Einreise in die Bundesrepublik Deutschland kann die Vorlage eines von den Behörden des ausländischen Staates ausgestellten amtlichen Gesundheitszeugnisses verlangt werden, aus dem hervorgeht, daß die Mitglieder ausländischer Streitkräfte frei von ansteckenden Krankheiten sind.</P><P>(6) Wird die öffentliche Sicherheit oder Ordnung der Bundesrepublik Deutschland durch ein ziviles oder militärisches Mitglied einer ausländischen Streitkraft gefährdet, so kann die Bundesrepublik Deutschland die unverzügliche Entfernung des Mitgliedes durch die ausländischen Streitkräfte verlangen. In der Vereinbarung ist zu bestimmen, daß die Behörden des Entsendestaates solchen Entfernungsersuchen nachzukommen und die Aufnahme des betreffenden Mitgliedes im eigenen Hoheitsgebiet zu gewährleisten haben. Im übrigen bleiben die Bestimmungen des Aufenthaltsgesetzes unberührt.</P>', 'toc': None, 'footnotes': None},
                    footnotes=None
                ),
            ]
        ),
        Heading(
            id='BJNR055429995BJNG000300305',
            name='Art 3',
            title=None,
            heading_level=0,
            children=[
                Article(
                    id='BJNR055429995BJNE002801311',
                    name='§ 1',
                    title=None,
                    body={'content': '<P>Das Bundesministerium der Verteidigung erläßt im Einvernehmen mit dem Bundesministerium des Innern, für Bau und Heimat allgemeine Verwaltungsvorschriften zur Ausführung des Artikels 2 § 5 über Besitz und Führen von Schußwaffen der diesem Gesetz unterfallenden ausländischen Militärangehörigen.</P>', 'toc': None, 'footnotes': None},
                    footnotes=None
                ),
                Article(
                    id='BJNR055429995BJNE002900305',
                    name='§ 2',
                    title=None,
                    body={'content': '<P>Der Verzicht auf die Ausübung der deutschen Gerichtsbarkeit gemäß Artikel 2 § 7 Abs. 2 wird von der Staatsanwaltschaft erklärt.</P>', 'toc': None, 'footnotes': None},
                    footnotes=None
                )
            ]
        ),
        Article(
            id='BJNR055429995BJNG000400305',
            name='Art 4',
            title=None,
            body={'content': '<P>Dieses Gesetz findet keine Anwendung auf <ABWFORMAT typ="A"/>Militärattaches eines ausländischen Staates in der Bundesrepublik Deutschland, die Mitglieder ihrer Stäbe sowie andere Militärpersonen, die in der Bundesrepublik Deutschland einen diplomatischen oder konsularischen Status haben.</P>', 'toc': None, 'footnotes': None},
            footnotes=None
        )
    ]
)
