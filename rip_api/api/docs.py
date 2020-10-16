tags_metadata = [
    {
        "name": "Laws",
        "description": "Federal legislation (Gesetze & Verordnungen)."
    },
    {
        "name": "Search",
        "description": "Full-text search in laws and articles."
    },
    {
        "name": "Bulk Downloads",
        "description": (
            "For easier integration into batch processing, we also provide regularly-updated bulk downloads containing "
            "all data available in this API."
        )
    }
]

description_api = """\
This API provides access to legal information for Germany.

For detailed information on this project (in German), see:
- [tech4germany/rechtsinfo_api](https://github.com/tech4germany/rechtsinfo_api) on Github and
- [the Tech4Germany website](https://tech.4germany.org/project/rechtsinformationsportal/).

### Note on text contents
<details>
  <summary><small>Click to expand</small></summary>

Text contents (mainly body and footnote text, but occasionally also text in law titles and item headings) are formatted in a custom XML format, which includes some HTML-like elements, but also many custom constructs. Absent any descriptive documentation, we have only been able to guess the format's semantics. We have included our guesses here, in the hope that they will be of use to consumers of this data.

Elements which exist in HTML with equivalent meaning include: `<P>`, `<pre>`, `<BR>`, `<SUB>`, `<SUP>`, `<B>`, `<I>`, `<U>`, `<small>`, `<IMG>`

Elements which exist in HTML but work differently:
- `<DL>/<DT>/<DD> and <LA>` - Definitions lists are used for enumerating paragraphs inside articles. `<DL>` attribute `Type` indicates the enumeration style (arabic/alpha/roman/etc), `Font` the text styles (normal/bold/italic/etc); `<DT>` holds the enumeration; `<DD>` holds the text content inside `<LA>` custom tags. (<a href="https://api.rechtsinformationsportal.de/v1/laws/amg/articles/BJNR024480976BJNE025900116">example</a>)
- `<table> etc` - The table format used in the data has some similarities to HTML but differs in many ways. It also bears some resemblance to the [CALS table model](https://www.oasis-open.org/specs/tablemodels.php) ([see also Wikipedia](https://en.wikipedia.org/wiki/CALS_Table_Model)). It uses `<row>` for table rows and `<entry>` for cell data. Other tags in use are: `<tgroup>`, `<thead>`, `<tfoot>`, `<tbody>`, `<colspec>`, `<spanspec>`.

Custom elements (with our buest guess at their meaning):

- `<F>` - Mathematical formulae (<a href="https://api.rechtsinformationsportal.de/v1/laws/zkg/articles/BJNR072010016BJNE005500000">example</a>)
- `<SP>` - Text with increased letter spacing (<a href="https://api.rechtsinformationsportal.de/v1/laws/fwistatv/articles/BJNR003610986BJNE000500326">example</a>)
- `<NB>` - No-wrap text (<a href="https://api.rechtsinformationsportal.de/v1/laws/eu_fahrgrbusv/articles/BJNR409800013BJNE000300000">example</a>)
- `<FnR>` - In-text reference to a footnote (<a href="https://api.rechtsinformationsportal.de/v1/laws/gwgmeldv_immobilien/articles/BJNR196500020BJNE000400000">example</a>)
- `<Footnote>` - Footnote text (<a href="https://api.rechtsinformationsportal.de/v1/laws/gwgmeldv_immobilien/articles/BJNR196500020BJNE000400000">example</a>)
- `<FnArea>` - Area for footnotes _inside_ body text (<a href="https://api.rechtsinformationsportal.de/v1/laws/euwo/articles/BJNR014530988BJNE012504377">example</a>)
- `<QuoteL>` - Opening quote marks (<a href="https://api.rechtsinformationsportal.de/v1/laws/medbvsv/articles/BJNR614700020BJNE000500000">example</a>)
- `<QuoteR>` - Closing quote marks (<a href="https://api.rechtsinformationsportal.de/v1/laws/medbvsv/articles/BJNR614700020BJNE000500000">example</a>)
- `<Title>` - Centered heading-styled text (<a href="https://api.rechtsinformationsportal.de/v1/laws/schbesv/articles/BJNR257500013BJNE001301305">example</a>)
- `<Subtitle>` - Centered subheading-styled text (<a href="https://api.rechtsinformationsportal.de/v1/laws/betrpraemdurchfg/articles/BJNR176310004BJNE001004377">example</a>)
- `<FILE>` - Links to file attachments, see also the "Note on attachments" below (<a href="https://api.rechtsinformationsportal.de/v1/laws/pstv/articles/BJNR226300008BJNE009100000">example</a>)
- `<Accolade>` - Used to indicate vertical lines in tables (<a href="https://api.rechtsinformationsportal.de/v1/laws/tabakerzv/articles/BJNR098010016BJNE003800000">example</a>)
- `<noindex>` - Unclear, possibly search-related? (<a href="https://api.rechtsinformationsportal.de/v1/laws/hhg/articles/BJNR004980955BJNE003402310">example</a>)
- `<Citation>` - Unclear, possibly like `<cite>` in HTML (<a href="https://api.rechtsinformationsportal.de/v1/laws/abfaev/articles/BJNR404310013BJNE000901116">example</a>)
- `<Split>` - Unclear, possibly a special line break (<a href="https://api.rechtsinformationsportal.de/v1/laws/ausbeignv_2009/articles/BJNR008800009BJNE001200000">example</a>)
- `<Ident>` - Unclear, used in tables of contents (<a href="https://api.rechtsinformationsportal.de/v1/laws/schausrv/articles/BJNR191310008BJNE000100000">example</a>)
- `<Revision>` - Unclear (<a href="https://api.rechtsinformationsportal.de/v1/laws/intguervg/articles/BJNR257310018BJNE001000000">example</a>)
- `<kommentar>` - Unclear (<a href="https://api.rechtsinformationsportal.de/v1/laws/binschuo/articles/BJNR139810018BJNE004800000">example</a>)
- `<ABWFORMAT>` - Unclear (<a href="https://api.rechtsinformationsportal.de/v1/laws/uelv_2_besvng/articles/BJNR026080975BJNE000501306">example</a>)

The complete format is specified (but not documented) at https://www.gesetze-im-internet.de/dtd/1.01/gii-norm.dtd.

For an example how this content can be processed and styled on a web page, see https://github.com/tech4germany/rechtsinfo-fe.

</details>

### Note on attachments
<details>
  <summary><small>Click to expand</small></summary>

Some laws reference attachments such as images or PDF documents by file name in their text contents. Laws returned by the API include an `attachments` field which maps the referenced file names to locations where these files are hosted publicly.

</details>

### Note on hierarchical sections in laws
<details>
  <summary><small>Click to expand</small></summary>

While some laws are simply collections of articles (_Paragrafen_ or _Artikel_), represented as content items with `type` "article", others are structured into sections with possibly several levels of subsections. To represent this, laws also include content items with `type` "heading" and articles have a `parent` field which points to the nearest heading they appear under. In some rare cases, section headings also include text content, which is represented by `type` "headingArticle".

To construct a hierarchical tree of sections, sub-sections, and articles, you can use this sample code:

##### Javascript
```javascript
// JSON response for a law including contents, e.g. https://api.rechtsinformationsportal.de/v1/laws/beeg?include=contents
const lawJson = ...;
const contentById = {};
const hierarchicalContents = [];
for (const item of lawJson.data.contents) {
    contentById[item.id] = item;
    item.children = [];

    if (item.parent === null) {
        hierarchicalContents.push(item);
    } else {
        parent = contentById[item.parent.id];
        parent.children.push(item);
    }
}
```

##### Python
```python
// JSON response for a law including contents, e.g. https://api.rechtsinformationsportal.de/v1/laws/beeg?include=contents
law_json = ...
content_by_id = {}
hierarchical_contents = []
for item in law_json['data']['contents']:
    content_by_id[item['id']] = item
    item['children'] = []

    if item['parent'] is None:
        hierarchical_contents.append(item)
    else:
        parent = content_by_id[item['parent']['id']]
        parent['children'].append(item)
```
</details>

"""

description_page = "Result page number"
description_per_page = "Number of items per page"
