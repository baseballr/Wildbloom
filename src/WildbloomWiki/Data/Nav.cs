namespace WildbloomWiki.Data;

public sealed record NavLink(string Title, string Href);
public sealed record NavGroup(string Title, IReadOnlyList<NavLink> Links);

/// <summary>The wiki sidebar. Guide links point at Lexicon chapters by slug.</summary>
public static class Nav
{
    public static readonly IReadOnlyList<NavGroup> Groups =
    [
        new("Overview",
        [
            new("Overview", ""),
            new("Getting Started", "guide/getting-started"),
            new("Progression", "guide/progression"),
        ]),
        new("Content",
        [
            new("Items", "items"),
            new("Blocks", "blocks"),
            new("Flowers", "flowers"),
            new("Bosses", "bosses"),
        ]),
        new("Systems",
        [
            new("Mana Pools", "guide/mana-pools"),
            new("Moving Mana", "guide/moving-mana"),
            new("Pool Infusion", "guide/pool-infusion"),
            new("Rune Altar", "guide/rune-altar"),
            new("Mana Enchanter", "guide/mana-enchanter"),
            new("Rituals", "guide/rituals"),
            new("Machines & Blocks", "guide/machines-blocks"),
        ]),
        new("Gear",
        [
            new("Tools & Weapons", "guide/tools-weapons"),
            new("Armor", "guide/armor"),
            new("Trinkets & Items", "guide/trinkets-items"),
        ]),
        new("Reference",
        [
            new("Recipes", "recipes"),
            new("Exploring", "guide/exploring"),
            new("Help & FAQ", "guide/help-faq"),
            new("Full Lexicon", "guide"),
        ]),
    ];
}
