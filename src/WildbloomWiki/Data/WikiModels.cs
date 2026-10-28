namespace WildbloomWiki.Data;

public sealed class WikiData
{
    public string Version { get; set; } = "";
    public string Download { get; set; } = "";
    public List<string> Categories { get; set; } = [];
    public List<Item> Items { get; set; } = [];
    public List<Recipe> Recipes { get; set; } = [];
    public Dictionary<string, string> Vanilla { get; set; } = [];
    public List<Flower> Flowers { get; set; } = [];
    public List<Helper> Helpers { get; set; } = [];
    public List<Boss> Bosses { get; set; } = [];
    public List<RuneEnchant> Enchantments { get; set; } = [];
    public List<Pool> Pools { get; set; } = [];
    public List<Guide> Guides { get; set; } = [];
}

public sealed class Item
{
    public string Id { get; set; } = "";
    public string Kind { get; set; } = "item";
    public string Name { get; set; } = "";
    public string Category { get; set; } = "";
    public string? Icon { get; set; }
    public string? Stats { get; set; }
    public List<string> Text { get; set; } = [];
    public string? Guide { get; set; }
    public int? Damage { get; set; }
    public int? Durability { get; set; }
    public int? Armor { get; set; }
    public int? Charge { get; set; }
    public int? Capacity { get; set; }
    public string? Effect { get; set; }

    public string Slug => Id.Split(':')[^1];
    public bool IsBlock => Kind == "block";
}

public sealed class Recipe
{
    public string Type { get; set; } = "";
    public string Output { get; set; } = "";
    public int Count { get; set; } = 1;
    public List<string>? Pattern { get; set; }
    public Dictionary<string, string>? Key { get; set; }
    public List<string> Ingredients { get; set; } = [];
    public int Cost { get; set; }
    public string? Station { get; set; }

    public string StationLabel => Type switch
    {
        "crafting" => "Crafting Table",
        "pool" => "Pool Infusion",
        "altar" => "Rune Altar",
        "brewery" => "Mana Brewery",
        _ => Type,
    };
}

public sealed class Flower
{
    public string Id { get; set; } = "";
    public int Tier { get; set; }
    public string Trigger { get; set; } = "";
    public int Output { get; set; }
    public List<FlowerFood> Accepts { get; set; } = [];
}

public sealed class FlowerFood
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public int Mana { get; set; }
}

public sealed class Helper
{
    public string Id { get; set; } = "";
    public int Radius { get; set; }
    public int Cost { get; set; }
}

public sealed class Boss
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public int Health { get; set; }
    public int Melee { get; set; }
    public string Key { get; set; } = "";
    public List<string> Summon { get; set; } = [];
    public List<string> Fight { get; set; } = [];
    public string Strategy { get; set; } = "";
    public List<BossDrop> Drops { get; set; } = [];
    public string Image { get; set; } = "";
    public int Order { get; set; }

    public string Slug => Id.Split(':')[^1];
}

public sealed class BossDrop
{
    public string Count { get; set; } = "";
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
}

public sealed class RuneEnchant
{
    public string Rune { get; set; } = "";
    public List<string> Enchants { get; set; } = [];
}

public sealed class Pool
{
    public string Id { get; set; } = "";
    public int Capacity { get; set; }
    public bool Overflow { get; set; }
}

public sealed class Guide
{
    public string Title { get; set; } = "";
    public string Slug { get; set; } = "";
    public List<string> Intro { get; set; } = [];
    public List<GuideSection> Sections { get; set; } = [];
}

public sealed class GuideSection
{
    public string Title { get; set; } = "";
    public string Slug { get; set; } = "";
    public List<string> Lines { get; set; } = [];
}
