using System.Net;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace WildbloomWiki.Data;

/// <summary>Loads data/wiki.json once and answers lookups for every page.</summary>
public sealed class WikiService(HttpClient http)
{
    static readonly JsonSerializerOptions Json = new() { PropertyNameCaseInsensitive = true };

    Task<WikiData>? _loading;
    Dictionary<string, Item> _byId = [];
    Dictionary<string, Item> _bySlug = [];
    Regex? _names;
    Dictionary<string, Item> _byName = [];
    Dictionary<string, (string Href, string Id)> _links = [];

    public WikiData Data { get; private set; } = new();

    public Task<WikiData> LoadAsync() => _loading ??= LoadCoreAsync();

    async Task<WikiData> LoadCoreAsync()
    {
        Data = await http.GetFromJsonAsync<WikiData>("data/wiki.json", Json) ?? new();
        _byId = Data.Items.ToDictionary(i => i.Id);
        _bySlug = Data.Items.ToDictionary(i => i.Slug);
        _byName = Data.Items.GroupBy(i => i.Name.ToLowerInvariant()).ToDictionary(g => g.Key, g => g.First());
        _links = Data.Items.GroupBy(i => i.Name.ToLowerInvariant()).ToDictionary(g => g.Key, g => (ItemHref(g.First()), g.First().Id));
        _links.TryAdd("livingwood", ("item/livingwood", "wb:livingwood"));
        foreach (var b in Data.Bosses)
            _links[b.Name.ToLowerInvariant()] = ($"bosses#{b.Slug}", b.Id);
        var alternatives = _links.Keys.OrderByDescending(k => k.Length).Select(Regex.Escape);
        _names = new Regex(@"\b(" + string.Join("|", alternatives) + @")s?\b", RegexOptions.IgnoreCase | RegexOptions.Compiled);
        return Data;
    }

    public Item? Item(string id) => _byId.GetValueOrDefault(id);
    public Item? ItemBySlug(string slug) => _bySlug.GetValueOrDefault(slug);
    public Item? ItemByName(string name) => _byName.GetValueOrDefault(name.ToLowerInvariant());

    public string Name(string id) =>
        _byId.TryGetValue(id, out var item) ? item.Name
        : Data.Vanilla.TryGetValue(id, out var v) ? v
        : id.Split(':')[^1].Replace('_', ' ');

    public IEnumerable<Recipe> RecipesFor(string id) => Data.Recipes.Where(r => r.Output == id);

    public IEnumerable<Recipe> RecipesUsing(string id) =>
        Data.Recipes.Where(r => r.Ingredients.Contains(id) && r.Output != id);

    public Flower? Flower(string id) => Data.Flowers.FirstOrDefault(f => f.Id == id);
    public Helper? Helper(string id) => Data.Helpers.FirstOrDefault(h => h.Id == id);
    public Guide? Guide(string slug) => Data.Guides.FirstOrDefault(g => g.Slug == slug);

    public static string ItemHref(Item item) => $"item/{item.Slug}";

    public static string GuideHref(string guide)
    {
        var parts = guide.Split('#', 2);
        return parts.Length == 2 ? $"guide/{parts[0]}#{parts[1]}" : $"guide/{parts[0]}";
    }

    /// <summary>HTML-encodes a line of Lexicon text and links every Wildbloom item named in it.</summary>
    public string Linkify(string text, string? skipId = null)
    {
        var encoded = WebUtility.HtmlEncode(text);
        if (_names is null) return encoded;
        var sb = new StringBuilder();
        var last = 0;
        foreach (Match m in _names.Matches(encoded))
        {
            var key = m.Groups[1].Value.ToLowerInvariant();
            if (!_links.TryGetValue(key, out var link) || link.Id == skipId) continue;
            sb.Append(encoded, last, m.Index - last);
            sb.Append($"<a class=\"item-ref\" href=\"{link.Href}\">{m.Value}</a>");
            last = m.Index + m.Length;
        }
        sb.Append(encoded, last, encoded.Length - last);
        return sb.ToString();
    }

    public IEnumerable<SearchHit> Search(string query)
    {
        query = query.Trim();
        if (query.Length == 0) yield break;
        var q = query.ToLowerInvariant();
        foreach (var item in Data.Items
                     .Where(i => i.Name.Contains(q, StringComparison.OrdinalIgnoreCase) || i.Category.Contains(q, StringComparison.OrdinalIgnoreCase))
                     .OrderBy(i => i.Name.StartsWith(q, StringComparison.OrdinalIgnoreCase) ? 0 : 1)
                     .ThenBy(i => i.Name)
                     .Take(12))
            yield return new SearchHit(item.Name, item.Category, ItemHref(item), item.Icon);

        foreach (var g in Data.Guides)
        {
            if (g.Title.Contains(q, StringComparison.OrdinalIgnoreCase))
                yield return new SearchHit(g.Title, "Guide", GuideHref(g.Slug), null);
            foreach (var s in g.Sections.Where(s => s.Title.Contains(q, StringComparison.OrdinalIgnoreCase)))
                yield return new SearchHit(s.Title, g.Title, GuideHref($"{g.Slug}#{s.Slug}"), null);
        }

        foreach (var b in Data.Bosses.Where(b => b.Name.Contains(q, StringComparison.OrdinalIgnoreCase)))
            yield return new SearchHit(b.Name, "Boss", $"bosses#{b.Slug}", b.Image);
    }
}

public sealed record SearchHit(string Title, string Section, string Href, string? Icon);
