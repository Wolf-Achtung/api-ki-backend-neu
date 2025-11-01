#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_research_system.py
=======================
Test-Script für das Research-System.

Usage:
    python test_research_system.py
"""
import os
import sys
import logging

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)


def test_env_vars():
    """Test 1: Prüfe Environment Variables."""
    print("\n" + "="*60)
    print("TEST 1: Environment Variables")
    print("="*60)
    
    required = ["TAVILY_API_KEY"]
    optional = ["PERPLEXITY_API_KEY", "USE_INTERNAL_RESEARCH", "RESEARCH_DEFAULT_DAYS"]
    
    all_ok = True
    
    for key in required:
        value = os.getenv(key)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else value
            print(f"✅ {key} = {masked}")
        else:
            print(f"❌ {key} = NOT SET (REQUIRED!)")
            all_ok = False
    
    for key in optional:
        value = os.getenv(key)
        if value:
            print(f"✅ {key} = {value}")
        else:
            print(f"ℹ️  {key} = not set (optional)")
    
    return all_ok


def test_imports():
    """Test 2: Prüfe Module-Imports."""
    print("\n" + "="*60)
    print("TEST 2: Module Imports")
    print("="*60)
    
    modules = [
        ("services.research_clients", "TavilyClient"),
        ("services.research_clients", "PerplexityClient"),
        ("services.research_policy", "ResearchPolicy"),
        ("services.research_policy", "queries_for_briefing"),
        ("services.research_pipeline", "run_research"),
        ("services.research_cache", "cache_get"),
        ("services.research_html", "items_to_html"),
    ]
    
    all_ok = True
    
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
        except ImportError as e:
            print(f"❌ {module_name}.{class_name} - Import Error: {e}")
            all_ok = False
        except AttributeError as e:
            print(f"❌ {module_name}.{class_name} - Not Found: {e}")
            all_ok = False
    
    return all_ok


def test_tavily_client():
    """Test 3: Teste Tavily Client."""
    print("\n" + "="*60)
    print("TEST 3: Tavily Client")
    print("="*60)
    
    try:
        from services.research_clients import TavilyClient
        
        client = TavilyClient()
        
        if not client.available():
            print("❌ Tavily Client not available (API key missing)")
            return False
        
        print("✅ Tavily Client initialized")
        
        # Test simple search
        print("🔍 Testing search: 'KI Tools Deutschland'...")
        results = client.search(
            "KI Tools Deutschland",
            days=7,
            max_results=3,
            apply_nsfw_filter=True
        )
        
        print(f"✅ Got {len(results)} results")
        
        if results:
            print(f"\nErster Result:")
            first = results[0]
            print(f"  Title: {first.get('title', 'N/A')[:80]}")
            print(f"  URL: {first.get('url', 'N/A')}")
            print(f"  Source: {first.get('source', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tavily test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_generation():
    """Test 4: Teste Query-Generierung."""
    print("\n" + "="*60)
    print("TEST 4: Query Generation")
    print("="*60)
    
    try:
        from services.research_policy import queries_for_briefing
        
        test_briefing = {
            "branche": "Maschinenbau",
            "bundesland": "BY",
            "hauptleistung": "Präzisionsteile",
            "ki_ziele": ["Automatisierung", "Qualitätskontrolle"]
        }
        
        queries = queries_for_briefing(test_briefing)
        
        print(f"✅ Generated {len(queries)} query categories")
        
        for category, query_list in queries.items():
            print(f"\n{category.upper()}: {len(query_list)} queries")
            for i, q in enumerate(query_list[:2], 1):  # Zeige nur erste 2
                print(f"  {i}. {q}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_nsfw_filter():
    """Test 5: Teste NSFW-Filter."""
    print("\n" + "="*60)
    print("TEST 5: NSFW Filter")
    print("="*60)
    
    try:
        from services.research_clients import _is_safe_content
        
        test_cases = [
            {
                "title": "KI Tools für Marketing 2024",
                "url": "https://heise.de/ki-tools",
                "snippet": "Eine Übersicht über KI-gestützte Marketing-Tools",
                "expected": True,
                "desc": "Clean content"
            },
            {
                "title": "XXX Adult Content",
                "url": "https://xvideos.com/test",
                "snippet": "Adult porn content",
                "expected": False,
                "desc": "NSFW content"
            },
            {
                "title": "ChatGPT Tutorial",
                "url": "https://openai.com/blog/chatgpt",
                "snippet": "How to use ChatGPT effectively",
                "expected": True,
                "desc": "Safe content"
            }
        ]
        
        all_ok = True
        
        for i, case in enumerate(test_cases, 1):
            result = _is_safe_content(case["title"], case["url"], case["snippet"])
            expected = case["expected"]
            status = "✅" if result == expected else "❌"
            
            print(f"{status} Test {i} ({case['desc']}): {result} == {expected}")
            
            if result != expected:
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"❌ NSFW filter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache():
    """Test 6: Teste Cache-System."""
    print("\n" + "="*60)
    print("TEST 6: Cache System")
    print("="*60)
    
    try:
        from services.research_cache import cache_get, cache_set, cache_stats, cache_clear
        
        # Test write
        test_key = "test_key_12345"
        test_data = {"test": "data", "timestamp": "2024-11-01"}
        
        cache_set(test_key, test_data)
        print(f"✅ Cache write successful")
        
        # Test read
        cached = cache_get(test_key)
        if cached == test_data:
            print(f"✅ Cache read successful")
        else:
            print(f"❌ Cache read mismatch: {cached} != {test_data}")
            return False
        
        # Test stats
        stats = cache_stats()
        print(f"ℹ️  Cache stats: {stats['total_files']} files, {stats['total_size_bytes']} bytes")
        
        # Cleanup
        cache_clear(test_key)
        print(f"✅ Cache cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_html_generation():
    """Test 7: Teste HTML-Generierung."""
    print("\n" + "="*60)
    print("TEST 7: HTML Generation")
    print("="*60)
    
    try:
        from services.research_html import items_to_html, items_to_table
        
        test_items = [
            {
                "title": "Test Tool 1",
                "url": "https://example.com/tool1",
                "snippet": "This is a test tool for demonstration"
            },
            {
                "title": "Test Tool 2",
                "url": "https://example.com/tool2",
                "snippet": "Another test tool"
            }
        ]
        
        # Test list HTML
        html_list = items_to_html(test_items, title="Test Tools")
        if "<ul>" in html_list and "<li>" in html_list:
            print(f"✅ HTML list generation successful ({len(html_list)} chars)")
        else:
            print(f"❌ HTML list generation failed")
            return False
        
        # Test table HTML
        html_table = items_to_table(test_items, headers=["Tool", "URL"], columns=["title", "url"])
        if "<table" in html_table and "<tr>" in html_table:
            print(f"✅ HTML table generation successful ({len(html_table)} chars)")
        else:
            print(f"❌ HTML table generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ HTML generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Führe alle Tests aus."""
    print("\n" + "="*60)
    print("🧪 RESEARCH SYSTEM TEST SUITE")
    print("="*60)
    
    tests = [
        ("Environment Variables", test_env_vars),
        ("Module Imports", test_imports),
        ("Tavily Client", test_tavily_client),
        ("Query Generation", test_query_generation),
        ("NSFW Filter", test_nsfw_filter),
        ("Cache System", test_cache),
        ("HTML Generation", test_html_generation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
