from unittest import mock

from rip_api.gesetze_im_internet import parse_law_xml_to_dict


def test_parser():
    mock_open = mock.mock_open(read_data=XML_DATA)
    with mock.patch('rip_api.gesetze_im_internet.parsing.open', mock_open):
        law = parse_law_xml_to_dict('mock/xml/path.xml')

    assert law['doknr'] == 'BJNR055429995'
    assert law['abbreviation'] == 'SkAufG'
    assert law['extra_abbreviations'] == []
    assert law['first_published'] == '1995-07-20'
    assert law['source_timestamp'] == '20200722212521'
    assert law['heading_short'] == 'Streitkräfteaufenthaltsgesetz'
    assert law['heading_long'] == 'Gesetz über die Rechtsstellung ausländischer Streitkräfte bei\nvorübergehenden Aufenthalten in der Bundesrepublik Deutschland'
    assert law['publication_info'] == [{'periodical': 'BGBl II', 'reference': '1995, 554'}]
    assert law['status_info'] == [{'category': 'Stand', 'comment': 'Zuletzt geändert durch Art. 191 V v. 19.6.2020 I 1328'}]
    assert law['notes'] == {'body': None, 'documentary_footnotes': '<P><BR/> <pre xml:space="preserve">(+++ Textnachweis ab: 27.7.1995 +++)<BR/><BR/></pre></P>'}

    assert len(law['contents']) == 9

    item = law['contents'][0]
    assert item['item_type'] == 'article'
    assert item['doknr'] == 'BJNR055429995BJNE000600305'
    assert item['name'] == 'Eingangsformel'
    assert item['title'] == None
    assert item['body'] == {'content': '<P>Der Bundestag hat mit Zustimmung des Bundesrates das folgende Gesetz beschlossen:</P>', 'footnotes': None}
    assert item['documentary_footnotes'] == None
    assert item['content_level'] == 0
    assert item['parent'] == None

    item = law['contents'][1]
    assert item['item_type'] == 'article'
    assert item['doknr'] == 'BJNR055429995BJNG000100305'
    assert item['name'] == 'Art 1'
    assert item['title'] == None
    assert item['body'] == {'content': '<P>(1) Die Bundesregierung wird ermächtigt, Vereinbarungen mit ausländischen Staaten über Einreise und vorübergehenden Aufenthalt ihrer Streitkräfte in der Bundesrepublik Deutschland für Übungen, Durchreise auf dem Landwege und Ausbildung von Einheiten durch Rechtsverordnung ohne Zustimmung des Bundesrates in Kraft zu setzen.</P><P>(2) Vereinbarungen dürfen nur mit solchen Staaten geschlossen werden, die auch der Bundeswehr den Aufenthalt in ihrem Hoheitsgebiet gestatten.</P><P>(3) Die betroffenen Länder werden beteiligt.</P>', 'footnotes': None}
    assert item['documentary_footnotes'] == None
    assert item['content_level'] == 0
    assert item['parent'] == None

    item = law['contents'][2]
    assert item['item_type'] == 'heading_article'
    assert item['doknr'] == 'BJNR055429995BJNG000200305'
    assert item['name'] == 'Art 2'
    assert item['title'] == None
    assert item['body'] == {'content': '<P>In die Vereinbarungen werden, soweit nach ihrem Gegenstand und Zweck erforderlich, Regelungen mit folgendem Inhalt aufgenommen.</P>', 'footnotes': None}
    assert item['documentary_footnotes'] == None
    assert item['content_level'] == 0
    assert item['parent'] == None

    item = law['contents'][3]
    assert item['item_type'] == 'article'
    assert item['doknr'] == 'BJNR055429995BJNE000700305'
    assert item['name'] == '§ 1'
    assert item['title'] == 'Allgemeine Voraussetzungen'
    assert item['body'] == {'content': '<P>(1) Für Einreise und Aufenthalt bestimmen sich die Rechte und Pflichten der ausländischen Streitkräfte und ihrer Mitglieder nach den deutschen Gesetzen und Rechtsvorschriften.</P><P>(2) In der Vereinbarung sind die Rahmenbedingungen für den Aufenthalt der ausländischen Streitkräfte nach Art, Umfang und Dauer festzulegen.</P>', 'footnotes': None}
    assert item['documentary_footnotes'] == None
    assert item['content_level'] == 1
    assert item['parent'] == law['contents'][2]

    item = law['contents'][4]
    assert item['item_type'] == 'article'
    assert item['doknr'] == 'BJNR055429995BJNE000801310'
    assert item['name'] == '§ 2'
    assert item['title'] == 'Grenzübertritt, Einreise'
    assert item['body'] == {'content': '<P>(1) Ausländische Streitkräfte und deren Mitglieder sind im Rahmen dieses Gesetzes und der ausländerrechtlichen Vorschriften berechtigt, mit Land-, Wasser- und Luftfahrzeugen in die Bundesrepublik Deutschland einzureisen und sich in oder über dem Bundesgebiet aufzuhalten.</P><P>(2) Mitglieder ausländischer Streitkräfte, die zum militärischen Personal gehören, müssen beim Grenzübertritt mit sich führen entweder <DL Font="normal" Type="arabic"><DT>a)</DT><DD Font="normal"><LA Size="normal">einen gültigen Paß oder ein anerkanntes Paßersatzpapier oder</LA></DD> <DT>b)</DT><DD Font="normal"><LA Size="normal">einen amtlichen Lichtbildausweis, sofern sie in eine Sammelliste eingetragen sind und sich der Einheits- oder Verbandsführer durch einen gültigen Paß oder ein anerkanntes Paßersatzpapier ausweisen kann.</LA></DD> </DL> </P><P>(3) Mitglieder ausländischer Streitkräfte, die zum zivilen Personal gehören, müssen beim Grenzübertritt einen gültigen Paß oder ein anerkanntes Paßersatzpapier mit sich führen.</P><P>(4) Mitglieder ausländischer Streitkräfte weisen sich durch einen Paß, ein anerkanntes Paßersatzpapier oder, soweit sie zum militärischen Personal gehören, durch eine Sammelliste in Verbindung mit einem amtlichen Lichtbildausweis aus.</P><P>(5) Es gelten die internationalen und die deutschen Gesundheitsvorschriften. Bei der Einreise in die Bundesrepublik Deutschland kann die Vorlage eines von den Behörden des ausländischen Staates ausgestellten amtlichen Gesundheitszeugnisses verlangt werden, aus dem hervorgeht, daß die Mitglieder ausländischer Streitkräfte frei von ansteckenden Krankheiten sind.</P><P>(6) Wird die öffentliche Sicherheit oder Ordnung der Bundesrepublik Deutschland durch ein ziviles oder militärisches Mitglied einer ausländischen Streitkraft gefährdet, so kann die Bundesrepublik Deutschland die unverzügliche Entfernung des Mitgliedes durch die ausländischen Streitkräfte verlangen. In der Vereinbarung ist zu bestimmen, daß die Behörden des Entsendestaates solchen Entfernungsersuchen nachzukommen und die Aufnahme des betreffenden Mitgliedes im eigenen Hoheitsgebiet zu gewährleisten haben. Im übrigen bleiben die Bestimmungen des Aufenthaltsgesetzes unberührt.</P>', 'footnotes': None}
    assert item['documentary_footnotes'] == None
    assert item['content_level'] == 1
    assert item['parent'] == law['contents'][2]

    item = law['contents'][5]
    assert item['item_type'] == 'heading'
    assert item['doknr'] == 'BJNR055429995BJNG000300305'
    assert item['name'] == 'Art 3'
    assert item['title'] == None
    assert item['content_level'] == 0
    assert item['parent'] == None

    item = law['contents'][6]
    assert item['item_type'] == 'article'
    assert item['doknr'] == 'BJNR055429995BJNE002801311'
    assert item['name'] == '§ 1'
    assert item['title'] == None
    assert item['body'] == {'content': '<P>Das Bundesministerium der Verteidigung erläßt im Einvernehmen mit dem Bundesministerium des Innern, für Bau und Heimat allgemeine Verwaltungsvorschriften zur Ausführung des Artikels 2 § 5 über Besitz und Führen von Schußwaffen der diesem Gesetz unterfallenden ausländischen Militärangehörigen.</P>', 'footnotes': None}
    assert item['documentary_footnotes'] == None
    assert item['content_level'] == 1
    assert item['parent'] == law['contents'][5]

    item = law['contents'][7]
    assert item['item_type'] == 'article'
    assert item['doknr'] == 'BJNR055429995BJNE002900305'
    assert item['name'] == '§ 2'
    assert item['title'] == None
    assert item['body'] == {'content': '<P>Der Verzicht auf die Ausübung der deutschen Gerichtsbarkeit gemäß Artikel 2 § 7 Abs. 2 wird von der Staatsanwaltschaft erklärt.</P>', 'footnotes': None}
    assert item['documentary_footnotes'] == None
    assert item['content_level'] == 1
    assert item['parent'] == law['contents'][5]

    item = law['contents'][8]
    assert item['item_type'] == 'article'
    assert item['doknr'] == 'BJNR055429995BJNG000400305'
    assert item['name'] == 'Art 4'
    assert item['title'] == None
    assert item['body'] == {'content': '<P>Dieses Gesetz findet keine Anwendung auf <ABWFORMAT typ="A"/>Militärattaches eines ausländischen Staates in der Bundesrepublik Deutschland, die Mitglieder ihrer Stäbe sowie andere Militärpersonen, die in der Bundesrepublik Deutschland einen diplomatischen oder konsularischen Status haben.</P>', 'footnotes': None}
    assert item['documentary_footnotes'] == None
    assert item['content_level'] == 0
    assert item['parent'] == None


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
