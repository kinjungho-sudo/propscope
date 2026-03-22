import re

def parse_price(price_str: str) -> int:
    """
    "3억 2,000만원" -> 32000 (만원 단위 정수)
    "15,500만원" -> 15500
    "4억 5,000" -> 45000
    """
    if not price_str or not isinstance(price_str, str):
        return 0
        
    price_str = price_str.replace(",", "").strip()
    
    total = 0
    
    # "억" 앞의 숫자 파싱
    bill_match = re.search(r'(\d+)\s*억', price_str)
    if bill_match:
        total += int(bill_match.group(1)) * 10000
        
    # "억" 뒤의 숫자 또는 그냥 "만원" 앞의 숫자 파싱
    remain_str = price_str.split("억")[-1] if "억" in price_str else price_str
    
    # "5,000만원" 또는 "5,000" 매칭
    man_match = re.search(r'(\d+)', remain_str)
    if man_match:
        # 단, "억" 뒤에 있는데 만원 단위가 없는 경우 "2,000" 처럼 올 때 처리
        total += int(man_match.group(1))
        
    return total

def format_price(price_man: int) -> str:
    """
    32000 -> "3억 2,000만원"
    """
    if price_man <= 0:
        return "정보없음"
        
    bill = price_man // 10000
    man = price_man % 10000
    
    res = []
    if bill > 0:
        res.append(f"{bill}억")
    if man > 0:
        res.append(f"{man:,}만원")
        
    return " ".join(res) if res else "0만원"
