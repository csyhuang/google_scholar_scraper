import os
import citation_utilities

# Input parameters by user
list_of_articles_to_check = {
    3225371177020252908: 100,   # Atmospheric blocking as a traffic jam in the jet stream
    10477703589246425643: 78,   # Local finite-amplitude wave activity as a diagnostic of anomalous weather events
    12098694703830025611: 22,   # Local wave activity budgets of the wintertime Northern Hemisphere: Implication...
    14468658417246256587: 19,   # Role of finite-amplitude Rossby waves and nonconservative processes in downward...
    17382647637759034075: 13,   # Local wave activity and the onset of blocking along a potential vorticity front
    15968917917766089864: 11,   # Role of finite-amplitude eddies and mixing in the life cycle of SSW
    5485128022826263690: 3}     # The 2021 Pacific Northwest heat wave and associated blocking...
citation_records_dir: str = 'citation_records'  # Name of directory where the retrieved citations will be exported to
json_path = None  # It can be some existing JSON file retrieved


if __name__ == '__main__':
    if not os.path.exists(citation_records_dir):
        os.makedirs(citation_records_dir)
        print(f"Directory '{citation_records_dir}' created.")

    if json_path:
        # *** Test citation manager with offline data ***
        citation_manager = citation_utilities.CitationManager(
            article_id=json_path.split('_')[0], citation_records_dir=citation_records_dir, json_file=json_path)
        citation_manager.output_citations()
    else:
        for article_id in list_of_articles_to_check:
            citation_manager = citation_utilities.CitationManager(
                article_id=article_id, citation_records_dir=citation_records_dir, json_file=json_path)
            citation_manager.output_citations()

