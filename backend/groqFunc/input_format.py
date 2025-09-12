from groq import Groq
import json
import os

task = """
To identify text that is not part of a contract, look for informal tone, shorthand, incomplete sentences, and lack of legal phrasing like “shall” or defined terms (e.g., “Employee”). Also check for contextual clues like mentions of meetings, action items, or phrases suggesting review or discussion rather than binding obligations.
Use the examples for inputs of non-contracts and contracts. Return the output in json format following the example output.
"""

example1 = """
Meeting Notes – Termination of Employment Discussion
- discussed termination process after confirmation
- either side (employee/company) can end with 1 mth notice
- alt: company can just end it immediately + pay in lieu of notice (even if employee resigns)
- on last day – employee to return all company stuff
- if items lost/damaged (except usual wear & tear), company can deduct cost from final pay (legal limits apply)
- co. can terminate w/o notice if serious issue
- eg. gross misconduct, AWOL (absent without leave), constant breach of contract
- not following instructions, negligence, poor perf
- fraud, dishonesty, or anything that could make co. look bad
- no payout owed apart from what’s already earned
- co. still holds rights to act even if delay in response – not a waiver
- action points: review current phrasing vs this summary, confirm if needs alignment or any clarifications
"""
output1 = '{"is_contract": false}'
example2 = """
Termination by Notice or Payment
- After confirmation, either Party may terminate the Employment with one (1) month notice.
- The Company reserves the right, whether the Employee resigns or is dismissed, to terminate the Employment forthwith and make a payment in lieu of notice.
- On Termination Date, the Employee must return all Company property which is in his possession. The Employee will be liable to reimburse the Company for any loss of or damage to such property, except for fair wear and tear. The amount of such loss or damage shall be deducted from his final salary in the limits provided by the applicable legislation.

Termination Without Notice
- The Company may also terminate the Appointment with immediate effect without notice and with no liability to make any further payment to the Employee (other than in respect of amounts accrued due at the date of termination) if the Employee:
    - Is guilty of any gross misconduct affecting the business of the Company;
    - Is absent from work without the permission of the Company;
    - Commits any serious or repeated breach or non-observance of any of the provisions of this Agreement or refuses or neglects to comply with any reasonable and lawful directions of the Board;
    - Is, in the reasonable opinion of the Board, negligent and incompetent in the performance of his duties; or
    - Commits any fraud or dishonesty or acts in any manner which in the opinion of the Company brings or is likely to bring the Company into disrepute or is materially adverse to the interests of the Company.
    - The rights of the Company under Clause 23 are without prejudice to any other rights that it might have at law to terminate the Appointment or to accept any breach of this Agreement by the Employee as having brought the Agreement to an end. Any delay by the Company in exercising its rights to terminate shall not constitute a waiver thereof.
"""
output2 = '{"is_contract": true}'

def main(input):
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY")
    )
    completion = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        messages=[
            {
                "role": "user",
                "content": f"### Example 1\ncontent:\n{example1}\noutput:\n{output1}\n\n### Example 2\ncontent:\n{example2}\noutput:\n{output2}\n\n### Task\n{task}\n\ninput:\n{input}"
            },
        ],
        temperature=0.2,
        max_completion_tokens=4096,
        top_p=0.9,
        stream=False,
        response_format={"type": "json_object"},
        stop=None,
    )

    try:
        data = json.loads(completion.choices[0].message.content)
        return data["is_contract"]
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON string: {e}")

if __name__ == "__main__":
    input = """
    Once someone’s confirmed in their role, either the employee or the company can end the employment by giving one month’s notice. That said, the company also has the option to end things immediately—whether it’s a resignation or a dismissal—by paying the employee in lieu of notice.

    On the last working day, the employee is expected to return all company property in their possession. If anything’s missing or damaged (aside from regular wear and tear), the cost may need to be reimbursed, and the company can deduct this from the final paycheck, as long as it's within the legal limits.

    There’s also a provision for immediate termination without notice if certain serious issues come up. This includes things like gross misconduct, being absent without permission, repeated or serious contract breaches, or refusing to follow reasonable instructions. It also covers situations where the employee is clearly negligent or underperforming, or if they act dishonestly or in a way that could damage the company’s reputation.

    Lastly, just because the company doesn’t act right away in these situations doesn’t mean it gives up its rights to do so later. So even if there’s a delay in action, those rights are still in place.
    """
    main(input)
